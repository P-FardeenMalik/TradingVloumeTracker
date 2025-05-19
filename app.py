from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from datetime import datetime
import os
from dotenv import load_dotenv
import aiohttp
import asyncio
import json
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Use PostgreSQL for production (Vercel) and SQLite for development
if os.getenv('VERCEL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trading_volume.db'

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Supported exchanges configuration
SUPPORTED_EXCHANGES = {
    'binance': {
        'base_url': 'https://api.binance.com',
        'volume_endpoint': '/api/v3/account',
        'headers': {'X-MBX-APIKEY': os.getenv('BINANCE_API_KEY')}
    },
    'bybit': {
        'base_url': 'https://api.bybit.com',
        'volume_endpoint': '/v5/account/wallet-balance',
        'headers': {'X-BAPI-API-KEY': os.getenv('BYBIT_API_KEY')}
    },
    'okx': {
        'base_url': 'https://www.okx.com',
        'volume_endpoint': '/api/v5/account/balance',
        'headers': {'OK-ACCESS-KEY': os.getenv('OKX_API_KEY')}
    },
    'mexc': {
        'base_url': 'https://api.mexc.com',
        'volume_endpoint': '/api/v3/account',
        'headers': {'X-MEXC-APIKEY': os.getenv('MEXC_API_KEY')}
    }
}

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    exchange_credentials = db.relationship('ExchangeCredential', backref='user', lazy=True)

class ExchangeCredential(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exchange = db.Column(db.String(50), nullable=False)
    api_key = db.Column(db.String(255), nullable=False)
    api_secret = db.Column(db.String(255), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Form Definitions
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/check-volume', methods=['POST'])
@login_required
async def check_volume():
    data = request.get_json()
    exchange = data.get('exchange')
    uid = data.get('uid')
    
    if not exchange or not uid:
        return jsonify({'error': 'Missing exchange or UID'}), 400
        
    try:
        volume = await get_exchange_volume(exchange, uid)
        return jsonify({'volume': volume})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

async def get_exchange_volume(exchange: str, uid: str) -> float:
    """Get trading volume for a specific exchange and UID."""
    if exchange not in SUPPORTED_EXCHANGES:
        raise ValueError(f"Unsupported exchange: {exchange}")
        
    exchange_config = SUPPORTED_EXCHANGES[exchange]
    
    async with aiohttp.ClientSession() as session:
        url = f"{exchange_config['base_url']}{exchange_config['volume_endpoint']}"
        headers = exchange_config['headers']
        params = {'uid': uid}
        
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return parse_volume_data(exchange, data)
            else:
                raise Exception(f"Error getting volume from {exchange}: {response.status}")

def parse_volume_data(exchange: str, data: dict) -> float:
    """Parse volume data from exchange response."""
    try:
        if exchange == 'binance':
            return float(data.get('totalAssetOfBtc', 0)) * get_btc_price()
        elif exchange == 'bybit':
            return float(data.get('totalWalletBalance', 0))
        elif exchange == 'okx':
            return float(data.get('totalEq', 0))
        elif exchange == 'mexc':
            return float(data.get('totalAssetOfBtc', 0)) * get_btc_price()
        return 0.0
    except Exception as e:
        raise Exception(f"Error parsing volume data: {str(e)}")

def get_btc_price() -> float:
    """Get current BTC price in USD."""
    # TODO: Implement BTC price fetching from an exchange
    return 50000.0  # Placeholder value

if not os.getenv('VERCEL'):
    with app.app_context():
        db.create_all()
    app.run(debug=True) 