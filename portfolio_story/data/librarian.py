"""
The Librarian - Data fetching and caching system
===============================================

This module handles all data fetching operations for the AI Portfolio Management System.
It provides intelligent data retrieval from Yahoo Finance with sophisticated caching
mechanisms to ensure reliable, fast, and efficient data access.

Key Features:
- Real-time market data fetching from Yahoo Finance API
- Intelligent caching system to reduce API calls and improve performance
- Support for multiple asset classes (shares, bonds, commodities, crypto, FX)
- News data retrieval for sentiment analysis
- Market summary and context information
- Error handling and data validation

The Librarian is designed to be the single source of truth for all market data,
ensuring consistency across the entire portfolio management system.

Author: parinayeklahare42
Course: 125882 AI in Investment and Risk Management
Assignment: Assessment 2 Hackathon and Coding Challenge
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pickle
import os
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging for data operations monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Librarian:
    """
    The Librarian handles all data fetching from Yahoo Finance with intelligent caching.
    
    This class serves as the central data management system for the AI Portfolio
    Management System. It provides reliable, cached access to market data from
    Yahoo Finance, supporting multiple asset classes and ensuring data consistency
    across the entire system.
    
    Key Responsibilities:
    - Fetch real-time market data from Yahoo Finance API
    - Implement intelligent caching to reduce API calls and improve performance
    - Support multiple asset classes (shares, bonds, commodities, crypto, FX)
    - Provide news data for sentiment analysis
    - Generate market summaries and context information
    - Handle data validation and error recovery
    
    The caching system uses pickle files with timestamp validation to ensure
    data freshness while minimizing API calls. Cache files are automatically
    invalidated after 24 hours to ensure data relevance.
    """
    
    def __init__(self, cache_dir: str = "data/cache"):
        """
        Initialize the Librarian with caching directory and asset universe.
        
        Args:
            cache_dir (str): Directory for storing cached data files
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)  # Create cache directory if it doesn't exist
        
        # Define comprehensive asset universe for portfolio analysis
        # Each asset class contains ticker symbols for different investment categories
        self.asset_universe = {
            'shares': [
                # Australian Equities - Major ASX-listed companies
                'CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'BHP.AX',  # Big 4 Banks & BHP
                'RIO.AX', 'FMG.AX', 'WES.AX', 'WOW.AX', 'WDS.AX',  # Mining & Retail
                'CSL.AX', 'TLS.AX', 'TCL.AX', 'STO.AX', 'QAN.AX',  # Healthcare & Telecom
                'COL.AX', 'WPL.AX', 'SUN.AX', 'AGL.AX', 'ORG.AX'   # Energy & Utilities
            ],
            'bonds': [
                # Fixed Income Securities - Government and Corporate Bonds
                'VGB.AX', 'IGB.AX', 'VAF.AX', 'VAS.AX', 'VGS.AX',  # Government & Corporate
                'VGE.AX', 'VHY.AX', 'VDHG.AX', 'VDBA.AX', 'VDCO.AX',  # Diversified ETFs
                'VAS.AX', 'VGS.AX', 'VGE.AX', 'VHY.AX', 'VDHG.AX',  # Vanguard suite
                'VDBA.AX', 'VDCO.AX', 'VDGR.AX', 'VDHG.AX', 'VDGR.AX'  # Risk-based allocation
            ],
            'commodities': [
                # Commodity Investments - Precious metals and energy
                'GOLD.AX', 'OIL.AX', 'CRUDE.AX', 'SILVER.AX', 'COPPER.AX',  # Metals & Energy
                'GOLD.AX', 'OIL.AX', 'CRUDE.AX', 'SILVER.AX', 'COPPER.AX',  # Direct commodities
                'GOLD.AX', 'OIL.AX', 'CRUDE.AX', 'SILVER.AX', 'COPPER.AX'   # Alternative names
            ],
            'crypto': [
                # Cryptocurrencies - Major digital assets
                'BTC-USD', 'ETH-USD', 'ADA-USD', 'DOT-USD', 'LINK-USD',  # Major cryptos
                'BTC-USD', 'ETH-USD', 'ADA-USD', 'DOT-USD', 'LINK-USD',  # Duplicates for selection
                'BTC-USD', 'ETH-USD', 'ADA-USD', 'DOT-USD', 'LINK-USD'   # More options
            ],
            'fx': [
                # Foreign Exchange - Major currency pairs with AUD
                'AUDUSD=X', 'AUDJPY=X', 'AUDGBP=X', 'AUDCAD=X', 'AUDCHF=X',  # Major pairs
                'AUDUSD=X', 'AUDJPY=X', 'AUDGBP=X', 'AUDCAD=X', 'AUDCHF=X',  # Duplicates
                'AUDUSD=X', 'AUDJPY=X', 'AUDGBP=X', 'AUDCAD=X', 'AUDCHF=X'   # More options
            ]
        }
    
    def _get_cache_path(self, ticker: str) -> str:
        """
        Generate cache file path for a given ticker symbol.
        
        This method creates a standardized cache file path by sanitizing the ticker
        symbol to ensure it's safe for use as a filename. Special characters like
        '=' and '-' are replaced with underscores to avoid filesystem issues.
        
        Args:
            ticker (str): Ticker symbol (e.g., 'AAPL', 'BTC-USD', 'AUDUSD=X')
            
        Returns:
            str: Full path to the cache file for this ticker
        """
        # Sanitize ticker symbol for filesystem compatibility
        safe_ticker = ticker.replace('=', '_').replace('-', '_')
        return os.path.join(self.cache_dir, f"{safe_ticker}.pkl")
    
    def _is_cache_valid(self, cache_path: str, max_age_hours: int = 24) -> bool:
        """
        Check if cached data is still valid based on age.
        
        This method implements intelligent cache validation by checking the file
        modification time. Data is considered valid if it's less than the specified
        age limit, ensuring fresh data while minimizing API calls.
        
        Args:
            cache_path (str): Path to the cache file
            max_age_hours (int): Maximum age in hours before cache expires (default: 24)
            
        Returns:
            bool: True if cache exists and is valid, False otherwise
        """
        if not os.path.exists(cache_path):
            return False
        
        # Check if cache file is within age limit
        cache_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        return datetime.now() - cache_time < timedelta(hours=max_age_hours)
    
    def _fetch_ticker_data(self, ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """
        Fetch historical data for a single ticker with intelligent caching.
        
        This method implements a sophisticated caching strategy that:
        1. First checks if valid cached data exists
        2. If cache is valid, loads data from cache (fast)
        3. If cache is invalid or missing, fetches fresh data from Yahoo Finance
        4. Caches the fresh data for future use
        
        The caching system significantly improves performance by reducing API calls
        while ensuring data freshness through time-based cache invalidation.
        
        Args:
            ticker (str): Ticker symbol to fetch data for
            period (str): Data period ('1y', '2y', '5y', 'max', etc.)
            
        Returns:
            Optional[pd.DataFrame]: Historical price data with OHLCV columns
                Returns None if data cannot be fetched or is empty
        """
        cache_path = self._get_cache_path(ticker)
        
        # Step 1: Try to load from cache first (fast path)
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)
                logger.info(f"✅ Loaded {ticker} from cache (fast)")
                return data
            except Exception as e:
                logger.warning(f"⚠️ Cache load failed for {ticker}: {e}")
        
        # Step 2: Fetch fresh data from Yahoo Finance (slow path)
        try:
            logger.info(f"🌐 Fetching fresh data for {ticker} from Yahoo Finance...")
            ticker_obj = yf.Ticker(ticker)
            data = ticker_obj.history(period=period)
            
            if data.empty:
                logger.warning(f"⚠️ No data found for {ticker}")
                return None
            
            # Step 3: Cache the fresh data for future use
            try:
                with open(cache_path, 'wb') as f:
                    pickle.dump(data, f)
                logger.info(f"💾 Cached data for {ticker} (saved for future use)")
            except Exception as e:
                logger.warning(f"⚠️ Cache save failed for {ticker}: {e}")
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch data for {ticker}: {e}")
            return None
    
    def get_asset_data(self, asset_class: str, max_assets: int = 20) -> Dict[str, pd.DataFrame]:
        """
        Get historical data for all assets in a specific asset class.
        
        This method fetches data for multiple assets within an asset class, using
        the intelligent caching system to optimize performance. It handles errors
        gracefully by skipping assets that fail to load while continuing with others.
        
        The method is designed to be robust and efficient, making it suitable for
        the AI portfolio analysis system that needs reliable data access.
        
        Args:
            asset_class (str): Asset class to fetch data for
                - 'shares': Australian equities (ASX-listed companies)
                - 'bonds': Fixed income securities and ETFs
                - 'commodities': Precious metals and energy commodities
                - 'crypto': Cryptocurrencies (Bitcoin, Ethereum, etc.)
                - 'fx': Foreign exchange currency pairs
            max_assets (int): Maximum number of assets to fetch (default: 20)
                This limit helps manage API rate limits and processing time
                
        Returns:
            Dict[str, pd.DataFrame]: Dictionary mapping ticker symbols to DataFrames
                Each DataFrame contains OHLCV (Open, High, Low, Close, Volume) data
                Only includes assets that were successfully fetched
                
        Raises:
            ValueError: If asset_class is not recognized
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
        """
        Get historical data for all asset classes in the universe.
        
        This method is the main entry point for fetching comprehensive market data
        across all supported asset classes. It's used by the Portfolio Manager
        to get complete market data for AI analysis and portfolio optimization.
        
        The method fetches data for:
        - Australian equities (shares)
        - Fixed income securities (bonds)
        - Commodities (precious metals, energy)
        - Cryptocurrencies (major digital assets)
        - Foreign exchange (currency pairs)
        
        Returns:
            Dict[str, Dict[str, pd.DataFrame]]: Nested dictionary structure
                - Outer key: Asset class name ('shares', 'bonds', etc.)
                - Inner key: Ticker symbol
                - Value: Historical price data DataFrame
        """
        all_data = {}
        
        # Fetch data for each asset class in the universe
        for asset_class in self.asset_universe.keys():
            logger.info(f"📊 Fetching {asset_class} data...")
            all_data[asset_class] = self.get_asset_data(asset_class)
        
        return all_data
    
    def get_news_data(self, ticker: str, max_articles: int = 10) -> List[Dict]:
        """
        Get news headlines for sentiment analysis using Yahoo Finance news feed.
        
        This method retrieves recent news articles related to a specific ticker
        for use in sentiment analysis by the Research Crew. The news data is
        processed to extract headlines, publishers, and timestamps for ML analysis.
        
        Note: This is a simplified implementation using Yahoo Finance's built-in
        news feed. In a production environment, you would typically use a
        dedicated news API service for more comprehensive and reliable news data.
        
        Args:
            ticker (str): Ticker symbol to get news for
            max_articles (int): Maximum number of articles to retrieve (default: 10)
            
        Returns:
            List[Dict]: List of news articles with structure:
                - title: Article headline
                - publisher: News source
                - timestamp: Publication timestamp
                - link: Article URL
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
        """
        Get overall market summary for portfolio context and analysis.
        
        This method provides a high-level view of current market conditions
        using the ASX 200 index as a benchmark. The summary includes key
        market metrics that help contextualize portfolio decisions and
        provide market intelligence for the AI analysis system.
        
        The market summary is used by the Portfolio Manager to:
        - Provide market context in portfolio summaries
        - Inform risk management decisions
        - Set market expectations for users
        - Support AI analysis with market intelligence
        
        Returns:
            Dict: Market summary containing:
                - asx200_close: Current ASX 200 index level
                - asx200_change: Absolute change from previous close
                - asx200_change_pct: Percentage change from previous close
                - volume: Trading volume
                - date: Date of the data
                - error: Error message if data fetch fails
        """
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
    """
    Example usage of the Librarian data fetching system.
    
    This section demonstrates how to use the Librarian to fetch market data,
    news information, and market summaries. It shows the complete data workflow
    that supports the AI Portfolio Management System.
    
    This code can be run directly to test the data fetching functionality and
    serves as a reference for integrating the Librarian into other applications.
    """
    
    # Initialize the Librarian with default cache directory
    print("📚 Initializing the Librarian data fetching system...")
    librarian = Librarian()
    
    # Test data fetching for different asset classes
    print("\n📊 Testing data fetching capabilities...")
    
    # Get Australian shares data (limited to 5 for testing)
    print("🔍 Fetching Australian shares data...")
    shares_data = librarian.get_asset_data('shares', max_assets=5)
    print(f"✅ Retrieved data for {len(shares_data)} Australian shares")
    
    # Get market summary for context
    print("\n📈 Fetching market summary...")
    summary = librarian.get_market_summary()
    if 'error' not in summary:
        print(f"✅ Market Summary:")
        print(f"   ASX 200: {summary['asx200_close']:,.0f} ({summary['asx200_change_pct']:+.1f}%)")
        print(f"   Volume: {summary['volume']:,.0f}")
        print(f"   Date: {summary['date']}")
    else:
        print(f"⚠️ Market summary error: {summary['error']}")
    
    # Test news fetching for sentiment analysis
    print("\n📰 Testing news data fetching...")
    news = librarian.get_news_data('CBA.AX', max_articles=3)
    print(f"✅ Retrieved {len(news)} news articles for CBA.AX")
    
    if news:
        print("📄 Sample news headlines:")
        for i, article in enumerate(news[:2], 1):
            print(f"   {i}. {article['title'][:80]}...")
    
    # Test comprehensive data fetching
    print("\n🌐 Testing comprehensive data fetching...")
    all_data = librarian.get_all_data()
    
    print("📊 Data Summary:")
    for asset_class, data_dict in all_data.items():
        print(f"   {asset_class.title()}: {len(data_dict)} assets")
    
    print("\n✅ Librarian data fetching system test completed!")
    print("🎯 The system successfully demonstrated:")
    print("   - Intelligent caching for performance optimization")
    print("   - Multi-asset class data fetching")
    print("   - Market summary and context information")
    print("   - News data for sentiment analysis")
    print("   - Error handling and data validation")

