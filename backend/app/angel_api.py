import os
import pandas as pd
import logging
import pyotp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from SmartApi import SmartConnect

logger = logging.getLogger(__name__)

class AngelOneAPI:
    """Class to handle Angel One API integration for market data"""
    
    # Mapping of sector indices to their Angel One token IDs
    SECTOR_INDICES = {
        'NIFTY 50': '26000',
        'NIFTY BANK': '26009',
    }
    
    def __init__(self):
        """Initialize Angel One API connection"""
        self.api = None
        self.connected = False
        self.api_key = os.getenv("ANGEL_API_KEY", "")
        self.client_id = os.getenv("ANGEL_CLIENT_ID", "")
        self.password = os.getenv("ANGEL_PASSWORD", "")
        self.totp_key = os.getenv("ANGEL_TOTP_KEY", "")
        
        # Connect to API if credentials are available
        if self.api_key and self.client_id and self.password and self.totp_key:
            self.connect()
    
    def connect(self) -> bool:
        """Connect to Angel One API"""
        try:
            # Generate TOTP
            totp = pyotp.TOTP(self.totp_key)
            totp_value = totp.now()
            
            # Initialize API
            self.api = SmartConnect(api_key=self.api_key)
            
            # Login
            data = self.api.generateSession(self.client_id, self.password, totp_value)
            
            if data.get('status'):
                self.connected = True
                logger.info("Successfully connected to Angel One API")
                return True
            else:
                logger.error(f"Failed to connect to Angel One API: {data.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to Angel One API: {str(e)}")
            return False
    
    def get_historical_data(self, symbol_token: str, interval: str, from_date: datetime, to_date: datetime) -> pd.DataFrame:
        """Get historical data for a symbol (legacy method)""" 
        # This method is kept for backward compatibility
        return self.get_historical_data_angel(symbol_token, interval, from_date, to_date)

    def test_index_data_availability(self, symbol_name: str, symbol_token: str) -> Dict: 
        """Test if historical data is available for an index""" 
        if not self.connected: 
            if not self.connect(): 
                return {'available': False, 'error': 'Not connected'} 
        
        try: 
            # Test with a small date range (last 5 days) 
            end_date = datetime.now() 
            start_date = end_date - timedelta(days=5) 
            
            result = self.get_historical_data_angel( 
                symbol_token, 
                "ONE_DAY", 
                start_date, 
                end_date 
            ) 
            
            if not result.empty: 
                return { 
                    'available': True, 
                    'data_points': len(result), 
                    'date_range': f"{result.index[0]} to {result.index[-1]}" 
                } 
            else: 
                return {'available': False, 'error': 'No data returned'} 
                
        except Exception as e: 
            return {'available': False, 'error': str(e)} 

    def get_historical_data_angel(self, symbol_token: str, interval: str, 
                                from_date: datetime, to_date: datetime) -> pd.DataFrame: 
        """Get historical data from Angel One API""" 
        if not self.connected: 
            if not self.connect(): 
                logger.error("Cannot fetch historical data: Not connected to API") 
                return pd.DataFrame() 
        
        try: 
            # Format dates 
            from_date_str = from_date.strftime('%Y-%m-%d %H:%M') 
            to_date_str = to_date.strftime('%Y-%m-%d %H:%M') 
            
            # Get historical data - Correct method signature 
            historicParam = { 
                "symboltoken": symbol_token, 
                "interval": interval, 
                "fromdate": from_date_str, 
                "todate": to_date_str 
            } 
            
            data = self.api.getCandleData(historicParam) 
            
            if data.get('status') and data.get('data'): 
                # Convert to DataFrame 
                candles = data.get('data', []) 
                if not candles: 
                    return pd.DataFrame() 
                
                df = pd.DataFrame( 
                    candles, 
                    columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'] 
                ) 
                
                # Convert timestamp to datetime 
                df['Timestamp'] = pd.to_datetime(df['Timestamp']) 
                df.set_index('Timestamp', inplace=True) 
                
                # Convert to numeric 
                numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume'] 
                df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors='coerce') 
                
                return df 
            else: 
                logger.warning(f"Angel One API returned no data: {data.get('message')}") 
                return pd.DataFrame() 
                
        except Exception as e: 
            logger.error(f"Error getting Angel One data: {str(e)}") 
            return pd.DataFrame()
    
    def get_sector_data(self, sector_name: str, period: str) -> Tuple[pd.DataFrame, bool]:
        """Get data for a specific sector index"""
        if sector_name not in self.SECTOR_INDICES:
            logger.error(f"Sector {sector_name} not found in available indices")
            return pd.DataFrame(), False
        
        symbol_token = self.SECTOR_INDICES[sector_name]
        logger.info(f"Fetching data for {sector_name} with token {symbol_token}")
        
        # Determine date range and interval based on period
        now = datetime.now()
        if period == "1d":
            from_date = now - timedelta(days=5)  # Get 5 days to ensure we have enough data
            interval = "ONE_DAY"
        elif period == "7d":
            from_date = now - timedelta(days=30)  # Get 1 month to calculate 7-day performance
            interval = "ONE_DAY"
        elif period == "30d":
            from_date = now - timedelta(days=90)  # Get 3 months to calculate 30-day performance
            interval = "ONE_DAY"
        elif period == "90d":
            from_date = now - timedelta(days=180)  # Get 6 months to calculate 90-day performance
            interval = "ONE_DAY"
        elif period == "52w":
            from_date = now - timedelta(days=730)  # Get 2 years to calculate 52-week performance
            interval = "ONE_DAY"
        else:
            from_date = now - timedelta(days=5)
            interval = "ONE_DAY"
        
        # Get historical data
        df = self.get_historical_data(symbol_token, interval, from_date, now)
        
        if df.empty:
            logger.warning(f"No data returned for {sector_name} with token {symbol_token}")
            return df, False
        
        logger.info(f"Successfully fetched {len(df)} data points for {sector_name}")
        return df, True