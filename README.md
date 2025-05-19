# Trading Volume Checker Web Application

A web application that allows users to check their trading volume across multiple cryptocurrency exchanges and maintain access to premium channels based on volume requirements.

## Features

- User authentication (register/login)
- Real-time trading volume checking across multiple exchanges
- Support for Binance, Bybit, OKX, and MEXC exchanges
- Secure storage of exchange API credentials
- Modern and responsive UI
- Volume requirement monitoring

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd trading-volume-checker
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your environment variables:
```
SECRET_KEY=your-secret-key-here
BINANCE_API_KEY=your-binance-api-key
BYBIT_API_KEY=your-bybit-api-key
OKX_API_KEY=your-okx-api-key
MEXC_API_KEY=your-mexc-api-key
```

5. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

## Running the Application

1. Start the Flask development server:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## Project Structure

```
trading-volume-checker/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── static/               # Static files
│   ├── css/
│   │   └── style.css    # Custom styles
│   └── js/
│       └── main.js      # Client-side JavaScript
├── templates/            # HTML templates
│   ├── base.html        # Base template
│   ├── index.html       # Home page
│   ├── login.html       # Login page
│   ├── register.html    # Registration page
│   └── dashboard.html   # User dashboard
└── .env                 # Environment variables (create from .env.example)
```

## Security Considerations

- Never commit your `.env` file to version control
- Use strong passwords for user accounts
- Keep your exchange API keys secure
- Regularly update dependencies to patch security vulnerabilities

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 