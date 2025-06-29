import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from .angel_api import AngelOneAPI

logger = logging.getLogger(__name__)

class SectorDataHandler:
    """Handle fetching and processing of Indian Nifty sector performance data"""
    
    # Nifty sector indices with their names
    NIFTY_SECTORS = {
        'NIFTY IT': 'NIFTY IT',
        'NIFTY BANK': 'NIFTY BANK'
    }
    
    # Broader market indices for comparison
    BROADER_INDICES = {
        'NIFTY 50': 'NIFTY 50'

    }
    
    def __init__(self):
        self.all_symbols = {**self.NIFTY_SECTORS, **self.BROADER_INDICES}
        self.angel_api = AngelOneAPI()
    
    def fetch_sector_data(self, period: str = "1d") -> Dict:
        """
        Fetch sector performance data
        
        Args:
            period: Time period ('1d', '7d', '30d', '90d', '52w')
            
        Returns:
            Dictionary with sector performance data
        """
        try:
            sector_data = []
            
            for sector_name, sector_key in self.all_symbols.items():
                try:
                    # Fetch data for the sector using Angel One API
                    hist, success = self.angel_api.get_sector_data(sector_key, period)
                    
                    if not success or len(hist) < 2:
                        logger.warning(f"Insufficient data for {sector_name}")
                        continue
                    
                    # Calculate performance based on period
                    if period == "1d":
                        performance = self._calculate_daily_performance(hist)
                    elif period == "7d":
                        performance = self._calculate_weekly_performance(hist)
                    elif period == "30d":
                        performance = self._calculate_monthly_performance(hist)
                    elif period == "90d":
                        performance = self._calculate_quarterly_performance(hist)
                    elif period == "52w":
                        performance = self._calculate_yearly_performance(hist)
                    else:
                        performance = self._calculate_daily_performance(hist)
                    
                    sector_data.append({
                        'sector': sector_name,
                        'symbol': sector_key,
                        'performance': round(performance, 2),
                        'current_price': round(hist['Close'].iloc[-1], 2),
                        'previous_price': round(hist['Close'].iloc[-2], 2),
                        'volume': int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0,
                        'last_updated': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    logger.error(f"Error fetching data for {sector_name}: {str(e)}")
                    continue
            
            # Sort by performance (descending)
            sector_data.sort(key=lambda x: x['performance'], reverse=True)
            
            return {
                'success': True,
                'period': period,
                'data': sector_data,
                'timestamp': datetime.now().isoformat(),
                'total_sectors': len(sector_data)
            }
            
        except Exception as e:
            logger.error(f"Error in fetch_sector_data: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': [],
                'timestamp': datetime.now().isoformat()
            }
    
    def _calculate_daily_performance(self, hist: pd.DataFrame) -> float:
        """Calculate 1-day performance"""
        if len(hist) < 2:
            return 0.0
        
        current = hist['Close'].iloc[-1]
        previous = hist['Close'].iloc[-2]
        return ((current - previous) / previous) * 100
    
    def _calculate_weekly_performance(self, hist: pd.DataFrame) -> float:
        """Calculate 7-day cumulative performance"""
        if len(hist) < 8:  # Need at least 8 days to calculate 7-day performance
            return 0.0
        
        # Get price from 7 trading days ago
        current = hist['Close'].iloc[-1]
        week_ago = hist['Close'].iloc[-8]  # 7 trading days ago (including current day)
        
        return ((current - week_ago) / week_ago) * 100
    
    def _calculate_monthly_performance(self, hist: pd.DataFrame) -> float:
        """Calculate 30-day performance"""
        if len(hist) < 22:  # Approximately 22 trading days in a month
            return 0.0
        
        current = hist['Close'].iloc[-1]
        month_ago = hist['Close'].iloc[-22]
        
        return ((current - month_ago) / month_ago) * 100
    
    def _calculate_quarterly_performance(self, hist: pd.DataFrame) -> float:
        """Calculate 90-day performance"""
        if len(hist) < 65:  # Approximately 65 trading days in 3 months
            return 0.0
        
        current = hist['Close'].iloc[-1]
        quarter_ago = hist['Close'].iloc[-65]
        
        return ((current - quarter_ago) / quarter_ago) * 100
    
    def _calculate_yearly_performance(self, hist: pd.DataFrame) -> float:
        """Calculate 52-week performance"""
        if len(hist) < 252:  # Approximately 252 trading days in a year
            return 0.0
        
        current = hist['Close'].iloc[-1]
        year_ago = hist['Close'].iloc[-252]
        
        return ((current - year_ago) / year_ago) * 100
    
    def get_top_performers(self, period: str = "1d", limit: int = 5) -> List[Dict]:
        """Get top performing sectors"""
        data = self.fetch_sector_data(period)
        
        if not data['success']:
            return []
        
        return data['data'][:limit]
    
    def get_worst_performers(self, period: str = "1d", limit: int = 5) -> List[Dict]:
        """Get worst performing sectors"""
        data = self.fetch_sector_data(period)
        
        if not data['success']:
            return []
        
        return data['data'][-limit:]
    
    def get_sector_summary(self, period: str = "1d") -> Dict:
        """Get summary statistics for all sectors"""
        data = self.fetch_sector_data(period)
        
        if not data['success']:
            return {'error': 'Failed to fetch data'}
        
        performances = [item['performance'] for item in data['data']]
        
        # Check if performances list is empty
        if not performances:
            return {
                'error': 'No sector data available',
                'period': period,
                'total_sectors': 0,
                'timestamp': datetime.now().isoformat()
            }
        
        return {
            'period': period,
            'total_sectors': len(performances),
            'average_performance': round(np.mean(performances), 2),
            'median_performance': round(np.median(performances), 2),
            'best_performance': round(max(performances), 2),
            'worst_performance': round(min(performances), 2),
            'positive_sectors': len([p for p in performances if p > 0]),
            'negative_sectors': len([p for p in performances if p < 0]),
            'timestamp': datetime.now().isoformat()
        }