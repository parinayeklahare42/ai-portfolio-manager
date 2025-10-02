"""
The Research Crew - AI/ML analysis engine
Performs momentum, volatility, drawdown, and sentiment analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.preprocessing import StandardScaler
from textblob import TextBlob
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ResearchCrew:
    """
    The Research Crew performs four key analyses:
    1. Momentum (6 months): Has it been trending up?
    2. Volatility (last 20 days): How bumpy has it been?
    3. Max Drawdown (1 year): How bad was the worst drop?
    4. Headline tone: Recent news sentiment analysis
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
    
    def calculate_momentum_score(self, data: pd.DataFrame, lookback_days: int = 126) -> float:
        """
        Calculate 6-month momentum score
        
        Args:
            data: Price data with 'Close' column
            lookback_days: Number of days to look back (default 126 = ~6 months)
            
        Returns:
            Momentum score between 0 and 1 (higher = better momentum)
        """
        if len(data) < lookback_days:
            return 0.5  # Neutral score for insufficient data
        
        # Get recent and historical prices
        recent_price = data['Close'].iloc[-1]
        historical_price = data['Close'].iloc[-lookback_days]
        
        # Calculate momentum as percentage change
        momentum_pct = (recent_price - historical_price) / historical_price
        
        # Convert to 0-1 scale using sigmoid function
        # Positive momentum gets higher scores, negative gets lower
        momentum_score = 1 / (1 + np.exp(-momentum_pct * 10))  # Scale factor of 10
        
        return float(momentum_score)
    
    def calculate_volatility_score(self, data: pd.DataFrame, lookback_days: int = 20) -> float:
        """
        Calculate volatility score (lower volatility = higher score)
        
        Args:
            data: Price data with 'Close' column
            lookback_days: Number of days to look back
            
        Returns:
            Volatility score between 0 and 1 (higher = lower volatility = safer)
        """
        if len(data) < lookback_days:
            return 0.5  # Neutral score for insufficient data
        
        # Calculate daily returns
        returns = data['Close'].pct_change().dropna()
        recent_returns = returns.tail(lookback_days)
        
        # Calculate rolling volatility
        volatility = recent_returns.std() * np.sqrt(252)  # Annualized
        
        # Convert to score (lower volatility = higher score)
        # Use inverse relationship with cap at reasonable volatility levels
        max_volatility = 0.5  # 50% annual volatility as maximum
        volatility_score = max(0, 1 - (volatility / max_volatility))
        
        return float(volatility_score)
    
    def calculate_drawdown_score(self, data: pd.DataFrame, lookback_days: int = 252) -> float:
        """
        Calculate maximum drawdown score (lower drawdown = higher score)
        
        Args:
            data: Price data with 'Close' column
            lookback_days: Number of days to look back (default 252 = ~1 year)
            
        Returns:
            Drawdown score between 0 and 1 (higher = lower drawdown = safer)
        """
        if len(data) < lookback_days:
            return 0.5  # Neutral score for insufficient data
        
        # Calculate rolling maximum
        rolling_max = data['Close'].rolling(window=lookback_days, min_periods=1).max()
        
        # Calculate drawdown
        drawdown = (data['Close'] - rolling_max) / rolling_max
        
        # Get maximum drawdown (most negative value)
        max_drawdown = abs(drawdown.min())
        
        # Convert to score (lower drawdown = higher score)
        # Cap at 50% drawdown as maximum
        max_acceptable_drawdown = 0.5
        drawdown_score = max(0, 1 - (max_drawdown / max_acceptable_drawdown))
        
        return float(drawdown_score)
    
    def calculate_sentiment_score(self, news_data: List[Dict]) -> float:
        """
        Calculate sentiment score from news headlines
        
        Args:
            news_data: List of news articles with 'title' field
            
        Returns:
            Sentiment score between 0 and 1 (higher = more positive sentiment)
        """
        if not news_data:
            return 0.5  # Neutral score for no news
        
        sentiments = []
        
        for article in news_data:
            title = article.get('title', '')
            if title:
                # Use TextBlob for sentiment analysis
                blob = TextBlob(title)
                sentiment = blob.sentiment.polarity  # -1 to 1
                sentiments.append(sentiment)
        
        if not sentiments:
            return 0.5  # Neutral if no valid titles
        
        # Average sentiment and convert to 0-1 scale
        avg_sentiment = np.mean(sentiments)
        sentiment_score = (avg_sentiment + 1) / 2  # Convert from [-1,1] to [0,1]
        
        return float(sentiment_score)
    
    def analyze_asset(self, ticker: str, price_data: pd.DataFrame, news_data: List[Dict]) -> Dict:
        """
        Perform complete analysis on a single asset
        
        Args:
            ticker: Asset ticker symbol
            price_data: Historical price data
            news_data: News articles for sentiment analysis
            
        Returns:
            Dictionary with all analysis results
        """
        try:
            # Calculate all scores
            momentum_score = self.calculate_momentum_score(price_data)
            volatility_score = self.calculate_volatility_score(price_data)
            drawdown_score = self.calculate_drawdown_score(price_data)
            sentiment_score = self.calculate_sentiment_score(news_data)
            
            # Calculate composite score (equal weights)
            composite_score = (momentum_score + volatility_score + drawdown_score + sentiment_score) / 4
            
            # Get additional metrics
            current_price = price_data['Close'].iloc[-1]
            price_change = price_data['Close'].pct_change().iloc[-1]
            
            return {
                'ticker': ticker,
                'current_price': current_price,
                'price_change': price_change,
                'momentum_score': momentum_score,
                'volatility_score': volatility_score,
                'drawdown_score': drawdown_score,
                'sentiment_score': sentiment_score,
                'composite_score': composite_score,
                'analysis_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Analysis failed for {ticker}: {e}")
            return {
                'ticker': ticker,
                'error': str(e),
                'composite_score': 0.0
            }
    
    def analyze_asset_class(self, asset_class: str, data_dict: Dict[str, pd.DataFrame], 
                          news_dict: Optional[Dict[str, List[Dict]]] = None) -> List[Dict]:
        """
        Analyze all assets in a class and return ranked results
        
        Args:
            asset_class: Asset class name
            data_dict: Dictionary of ticker -> price data
            news_dict: Optional dictionary of ticker -> news data
            
        Returns:
            List of analysis results sorted by composite score
        """
        results = []
        
        for ticker, price_data in data_dict.items():
            # Get news data if available
            news_data = news_dict.get(ticker, []) if news_dict else []
            
            # Analyze the asset
            analysis = self.analyze_asset(ticker, price_data, news_data)
            results.append(analysis)
        
        # Sort by composite score (highest first)
        results.sort(key=lambda x: x.get('composite_score', 0), reverse=True)
        
        logger.info(f"Analyzed {len(results)} {asset_class} assets")
        return results
    
    def get_leaderboard(self, analysis_results: List[Dict], top_n: int = 10) -> pd.DataFrame:
        """
        Create a leaderboard DataFrame from analysis results
        
        Args:
            analysis_results: List of analysis results
            top_n: Number of top assets to include
            
        Returns:
            DataFrame with leaderboard
        """
        if not analysis_results:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(analysis_results)
        
        # Select top N and relevant columns
        top_assets = df.head(top_n)
        
        # Format for display
        display_cols = ['ticker', 'current_price', 'composite_score', 
                       'momentum_score', 'volatility_score', 'drawdown_score', 'sentiment_score']
        
        available_cols = [col for col in display_cols if col in top_assets.columns]
        leaderboard = top_assets[available_cols].copy()
        
        # Round numeric columns
        numeric_cols = leaderboard.select_dtypes(include=[np.number]).columns
        leaderboard[numeric_cols] = leaderboard[numeric_cols].round(4)
        
        return leaderboard

# Example usage and testing
if __name__ == "__main__":
    # Initialize the Research Crew
    crew = ResearchCrew()
    
    # Create sample data for testing
    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
    sample_data = pd.DataFrame({
        'Close': 100 + np.cumsum(np.random.randn(len(dates)) * 0.02),
        'Volume': np.random.randint(1000, 10000, len(dates))
    }, index=dates)
    
    # Test individual functions
    momentum = crew.calculate_momentum_score(sample_data)
    volatility = crew.calculate_volatility_score(sample_data)
    drawdown = crew.calculate_drawdown_score(sample_data)
    
    print(f"Sample Analysis:")
    print(f"Momentum Score: {momentum:.4f}")
    print(f"Volatility Score: {volatility:.4f}")
    print(f"Drawdown Score: {drawdown:.4f}")
    
    # Test sentiment analysis
    sample_news = [
        {'title': 'Company reports strong quarterly earnings'},
        {'title': 'Stock price surges on positive outlook'},
        {'title': 'Analysts upgrade rating to buy'}
    ]
    
    sentiment = crew.calculate_sentiment_score(sample_news)
    print(f"Sentiment Score: {sentiment:.4f}")

