"""
The Librarian - Data fetching and caching system
Fetches fresh data from Yahoo Finance with intelligent caching
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pickle
import os
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Librarian:
    """
    The Librarian handles all data fetching from Yahoo Finance
    with intelligent caching to ensure reliability
    """
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Asset universe definitions
        self.asset_universe = {
            'shares': [
                'CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'BHP.AX',  # Banks & Mining
                'RIO.AX', 'FMG.AX', 'WES.AX', 'WOW.AX', 'WDS.AX',  # Resources & Retail
                'CSL.AX', 'TLS.AX', 'TCL.AX', 'STO.AX', 'QAN.AX',  # Healthcare & Telecom
                'COL.AX', 'WPL.AX', 'SUN.AX', 'AGL.AX', 'ORG.AX'   # Energy & Utilities
            ],
            'bonds': [
                'VGB.AX', 'IGB.AX', 'VAF.AX', 'VAS.AX', 'VGS.AX',  # Government & Corporate
                'VGE.AX', 'VHY.AX', 'VDHG.AX', 'VDBA.AX', 'VDCO.AX',  # Diversified ETFs
                'VAS.AX', 'VGS.AX', 'VGE.AX', 'VHY.AX', 'VDHG.AX',  # Vanguard suite
                'VDBA.AX', 'VDCO.AX', 'VDGR.AX', 'VDHG.AX', 'VDGR.AX'  # Risk-based
            ],
            'commodities': [
                'GOLD.AX', 'OIL.AX', 'CRUDE.AX', 'SILVER.AX', 'COPPER.AX',  # Metals & Energy
                'GOLD.AX', 'OIL.AX', 'CRUDE.AX', 'SILVER.AX', 'COPPER.AX',  # Direct commodities
                'GOLD.AX', 'OIL.AX', 'CRUDE.AX', 'SILVER.AX', 'COPPER.AX'   # Alternative names
            ],
            'crypto': [
                'BTC-USD', 'ETH-USD', 'ADA-USD', 'DOT-USD', 'LINK-USD',  # Major cryptos
                'BTC-USD', 'ETH-USD', 'ADA-USD', 'DOT-USD', 'LINK-USD',  # Duplicates for selection
                'BTC-USD', 'ETH-USD', 'ADA-USD', 'DOT-USD', 'LINK-USD'   # More options
            ],
            'fx': [
                'AUDUSD=X', 'AUDJPY=X', 'AUDGBP=X', 'AUDCAD=X', 'AUDCHF=X',  # Major pairs
                'AUDUSD=X', 'AUDJPY=X', 'AUDGBP=X', 'AUDCAD=X', 'AUDCHF=X',  # Duplicates
                'AUDUSD=X', 'AUDJPY=X', 'AUDGBP=X', 'AUDCAD=X', 'AUDCHF=X'   # More options
            ]
        }
    
    def _get_cache_path(self, ticker: str) -> str:
        """Get cache file path for a ticker"""
        return os.path.join(self.cache_dir, f"{ticker.replace('=', '_').replace('-', '_')}.pkl")
    
    def _is_cache_valid(self, cache_path: str, max_age_hours: int = 24) -> bool:
        """Check if cache is still valid"""
        if not os.path.exists(cache_path):
            return False
        
        cache_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        return datetime.now() - cache_time < timedelta(hours=max_age_hours)
    
    def _fetch_ticker_data(self, ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """Fetch data for a single ticker with caching"""
        cache_path = self._get_cache_path(ticker)
        
        # Try to load from cache first
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)
                logger.info(f"Loaded {ticker} from cache")
                return data
            except Exception as e:
                logger.warning(f"Cache load failed for {ticker}: {e}")
        
        # Fetch fresh data
        try:
            logger.info(f"Fetching fresh data for {ticker}")
            ticker_obj = yf.Ticker(ticker)
            data = ticker_obj.history(period=period)
            
            if data.empty:
                logger.warning(f"No data found for {ticker}")
                return None
            
            # Cache the data
            try:
                with open(cache_path, 'wb') as f:
                    pickle.dump(data, f)
                logger.info(f"Cached data for {ticker}")
            except Exception as e:
                logger.warning(f"Cache save failed for {ticker}: {e}")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch data for {ticker}: {e}")
            return None
    
    def get_asset_data(self, asset_class: str, max_assets: int = 20) -> Dict[str, pd.DataFrame]:
        """
        Get data for all assets in a class
        
        Args:
            asset_class: 'shares', 'bonds', 'commodities', 'crypto', 'fx'
            max_assets: Maximum number of assets to return
            
        Returns:
            Dictionary mapping ticker symbols to DataFrames
        """
        if asset_class not in self.asset_universe:
            raise ValueError(f"Unknown asset class: {asset_class}")
        
        tickers = self.asset_universe[asset_class][:max_assets]
        data_dict = {}
        
        for ticker in tickers:
            data = self._fetch_ticker_data(ticker)
            if data is not None and not data.empty:
                data_dict[ticker] = data
            else:
                logger.warning(f"Skipping {ticker} due to missing data")
        
        logger.info(f"Retrieved data for {len(data_dict)} {asset_class} assets")
        return data_dict
    
    def get_all_data(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        """Get data for all asset classes"""
        all_data = {}
        
        for asset_class in self.asset_universe.keys():
            logger.info(f"Fetching {asset_class} data...")
            all_data[asset_class] = self.get_asset_data(asset_class)
        
        return all_data
    
    def get_news_data(self, ticker: str, max_articles: int = 10) -> List[Dict]:
        """
        Get news headlines for sentiment analysis
        Note: This is a simplified version - in production you'd use a proper news API
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            news = ticker_obj.news[:max_articles]
            
            # Extract headlines and timestamps
            news_data = []
            for article in news:
                news_data.append({
                    'title': article.get('title', ''),
                    'publisher': article.get('publisher', ''),
                    'timestamp': article.get('providerPublishTime', 0),
                    'link': article.get('link', '')
                })
            
            return news_data
            
        except Exception as e:
            logger.warning(f"Failed to fetch news for {ticker}: {e}")
            return []
    
    def get_market_summary(self) -> Dict:
        """Get overall market summary for context"""
        try:
            # Get ASX 200 as market benchmark
            asx200 = yf.Ticker("^AXJO")
            asx_data = asx200.history(period="5d")
            
            if asx_data.empty:
                return {"error": "No market data available"}
            
            latest = asx_data.iloc[-1]
            previous = asx_data.iloc[-2] if len(asx_data) > 1 else latest
            
            change = latest['Close'] - previous['Close']
            change_pct = (change / previous['Close']) * 100
            
            return {
                "asx200_close": latest['Close'],
                "asx200_change": change,
                "asx200_change_pct": change_pct,
                "volume": latest['Volume'],
                "date": latest.name.strftime('%Y-%m-%d')
            }
            
        except Exception as e:
            logger.error(f"Failed to get market summary: {e}")
            return {"error": str(e)}

# Example usage and testing
if __name__ == "__main__":
    # Initialize the Librarian
    librarian = Librarian()
    
    # Test data fetching
    print("Testing data fetching...")
    
    # Get shares data
    shares_data = librarian.get_asset_data('shares', max_assets=5)
    print(f"Retrieved {len(shares_data)} shares")
    
    # Get market summary
    summary = librarian.get_market_summary()
    print(f"Market summary: {summary}")
    
    # Test news fetching
    news = librarian.get_news_data('CBA.AX', max_articles=3)
    print(f"Retrieved {len(news)} news articles")

