import os
from telethon import TelegramClient, events
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
import asyncio
from datetime import datetime, timedelta
import logging
from typing import Dict, List
import aiohttp
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('volume_checker.log'),
        logging.StreamHandler()
    ]
)

# Telegram API credentials
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
CHANNEL_USERNAME = 'your_premium_channel_username'  # Replace with your channel username

# Minimum trading volume requirement (in USD)
MIN_VOLUME_REQUIREMENT = 150000

# Supported exchanges and their API endpoints
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
    },
    'bingx': {
        'base_url': 'https://api.bingx.com',
        'volume_endpoint': '/api/v1/account',
        'headers': {'X-BX-APIKEY': os.getenv('BINGX_API_KEY')}
    },
    'bitget': {
        'base_url': 'https://api.bitget.com',
        'volume_endpoint': '/api/v2/spot/account/assets',
        'headers': {'ACCESS-KEY': os.getenv('BITGET_API_KEY')}
    },
    'lbank': {
        'base_url': 'https://api.lbank.com',
        'volume_endpoint': '/v2/user/account',
        'headers': {'Authorization': os.getenv('LBANK_API_KEY')}
    }
}

class ExchangeVolumeChecker:
    def __init__(self, exchange_name: str, uid: str):
        self.exchange_name = exchange_name
        self.uid = uid
        self.exchange_config = SUPPORTED_EXCHANGES[exchange_name]
        
    async def get_volume(self) -> float:
        """Get trading volume for a specific exchange and UID."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.exchange_config['base_url']}{self.exchange_config['volume_endpoint']}"
                headers = self.exchange_config['headers']
                
                # Add UID to request parameters
                params = {'uid': self.uid}
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_volume(data)
                    else:
                        logging.error(f"Error getting volume from {self.exchange_name}: {response.status}")
                        return 0.0
        except Exception as e:
            logging.error(f"Error checking volume for {self.exchange_name}: {str(e)}")
            return 0.0
            
    def _parse_volume(self, data: Dict) -> float:
        """Parse volume data from exchange response."""
        try:
            if self.exchange_name == 'binance':
                return float(data.get('totalAssetOfBtc', 0)) * self._get_btc_price()
            elif self.exchange_name == 'bybit':
                return float(data.get('totalWalletBalance', 0))
            elif self.exchange_name == 'okx':
                return float(data.get('totalEq', 0))
            elif self.exchange_name == 'mexc':
                return float(data.get('totalAssetOfBtc', 0)) * self._get_btc_price()
            elif self.exchange_name == 'bingx':
                return float(data.get('totalEquity', 0))
            elif self.exchange_name == 'bitget':
                return float(data.get('totalAsset', 0))
            elif self.exchange_name == 'lbank':
                return float(data.get('totalAsset', 0))
            return 0.0
        except Exception as e:
            logging.error(f"Error parsing volume data from {self.exchange_name}: {str(e)}")
            return 0.0
            
    def _get_btc_price(self) -> float:
        """Get current BTC price in USD."""
        # TODO: Implement BTC price fetching from an exchange
        return 50000.0  # Placeholder value

class VolumeChecker:
    def __init__(self):
        self.client = TelegramClient('volume_checker_session', API_ID, API_HASH)
        
    async def get_channel_members(self) -> List[Dict]:
        """Get all members from the premium channel."""
        try:
            participants = []
            offset = 0
            limit = 100
            
            while True:
                result = await self.client(GetParticipantsRequest(
                    channel=CHANNEL_USERNAME,
                    filter=ChannelParticipantsSearch(''),
                    offset=offset,
                    limit=limit,
                    hash=0
                ))
                
                if not result.users:
                    break
                    
                for user in result.users:
                    participants.append({
                        'id': user.id,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name
                    })
                
                offset += len(result.users)
                if len(result.users) < limit:
                    break
                    
            return participants
        except Exception as e:
            logging.error(f"Error getting channel members: {str(e)}")
            return []

    async def check_trading_volume(self, user_id: int, uid: str) -> float:
        """
        Check trading volume for a user across all supported exchanges.
        Returns total volume in USD.
        """
        total_volume = 0.0
        
        for exchange_name in SUPPORTED_EXCHANGES:
            checker = ExchangeVolumeChecker(exchange_name, uid)
            volume = await checker.get_volume()
            total_volume += volume
            logging.info(f"User {user_id} - {exchange_name} volume: ${volume:,.2f}")
        
        return total_volume

    async def remove_low_volume_members(self):
        """Remove members with trading volume below the requirement."""
        members = await self.get_channel_members()
        removed_count = 0
        
        for member in members:
            try:
                # Get UID from member's profile or database
                uid = self._get_user_uid(member['id'])
                if not uid:
                    logging.warning(f"No UID found for member {member['username']}")
                    continue
                    
                volume = await self.check_trading_volume(member['id'], uid)
                
                if volume < MIN_VOLUME_REQUIREMENT:
                    # Remove member from channel
                    await self.client.edit_permissions(
                        CHANNEL_USERNAME,
                        member['id'],
                        view_messages=False
                    )
                    removed_count += 1
                    logging.info(f"Removed member {member['username']} with volume ${volume:,.2f}")
                    
            except Exception as e:
                logging.error(f"Error processing member {member['username']}: {str(e)}")
                
        logging.info(f"Removed {removed_count} members with low trading volume")

    def _get_user_uid(self, user_id: int) -> str:
        """
        Get user's UID from your database or storage.
        This method should be implemented based on how you store user UIDs.
        """
        # TODO: Implement UID retrieval from your database
        return ""

    async def run(self):
        """Main execution function."""
        try:
            await self.client.start()
            await self.remove_low_volume_members()
        except Exception as e:
            logging.error(f"Error in main execution: {str(e)}")
        finally:
            await self.client.disconnect()

if __name__ == "__main__":
    checker = VolumeChecker()
    asyncio.run(checker.run()) 