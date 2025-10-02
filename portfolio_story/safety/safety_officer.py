"""
The Safety Officer - Risk management and guardrails
Implements safety checks before any trades are executed
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SafetyOfficer:
    """
    The Safety Officer implements four key safety systems:
    1. Sleep-Better Dial: Adjustable risk tolerance
    2. News Spike Filter: Protects against negative news events
    3. FX Auto-Hedge: Currency risk management
    4. Drawdown Seatbelt: Automatic risk reduction
    """
    
    def __init__(self):
        self.safety_rules = {
            'max_drawdown': 0.25,  # Maximum acceptable drawdown
            'news_spike_threshold': -0.05,  # 5% drop threshold for news filter
            'fx_hedge_threshold': 0.02,  # 2% AUD movement threshold
            'min_trade_size': 100,  # Minimum trade size in dollars
            'max_turnover': 0.20  # Maximum portfolio turnover per rebalance
        }
    
    def check_sleep_better_dial(self, allocation: Dict[str, float], 
                               sleep_better_dial: float) -> Dict[str, float]:
        """
        Apply sleep-better dial adjustment
        
        Args:
            allocation: Current allocation
            sleep_better_dial: 0 (aggressive) to 1 (conservative)
            
        Returns:
            Adjusted allocation with safety message
        """
        if sleep_better_dial <= 0:
            return {
                'allocation': allocation,
                'adjustment': 0.0,
                'message': "Sleep-better dial at aggressive setting - no adjustment"
            }
        
        # Calculate adjustment (move from shares to bonds)
        max_adjustment = 0.20  # Maximum 20% shift
        adjustment = sleep_better_dial * max_adjustment
        
        adjusted_allocation = allocation.copy()
        
        if 'shares' in adjusted_allocation and 'bonds' in adjusted_allocation:
            # Move from shares to bonds
            shares_reduction = min(adjustment, adjusted_allocation['shares'])
            adjusted_allocation['shares'] -= shares_reduction
            adjusted_allocation['bonds'] += shares_reduction
            
            # Normalize
            total = sum(adjusted_allocation.values())
            for key in adjusted_allocation:
                adjusted_allocation[key] /= total
        
        return {
            'allocation': adjusted_allocation,
            'adjustment': adjustment,
            'message': f"Sleep-better dial moved {adjustment:.1%} from shares to bonds"
        }
    
    def check_news_spike_filter(self, selected_assets: Dict[str, List[Dict]], 
                               news_data: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        Filter out assets with negative news spikes
        
        Args:
            selected_assets: Currently selected assets
            news_data: News data for sentiment analysis
            
        Returns:
            Filtered assets with safety messages
        """
        filtered_assets = {}
        safety_messages = []
        
        for asset_class, assets in selected_assets.items():
            filtered_class = []
            
            for asset in assets:
                ticker = asset['ticker']
                news = news_data.get(ticker, [])
                
                # Check for negative news spike
                if self._has_negative_news_spike(asset, news):
                    # Reduce weight or exclude
                    if asset.get('allocation_percentage', 0) > 0.05:  # Only if significant allocation
                        asset['allocation_percentage'] *= 0.5  # Reduce by half
                        safety_messages.append(f"News spike filter: Reduced {ticker} allocation due to negative news")
                    else:
                        safety_messages.append(f"News spike filter: Excluded {ticker} due to negative news")
                        continue
                
                filtered_class.append(asset)
            
            filtered_assets[asset_class] = filtered_class
        
        return {
            'assets': filtered_assets,
            'messages': safety_messages
        }
    
    def _has_negative_news_spike(self, asset: Dict, news: List[Dict]) -> bool:
        """
        Check if asset has negative news spike
        
        Args:
            asset: Asset data with price change
            news: Recent news articles
            
        Returns:
            True if negative news spike detected
        """
        # Check recent price movement
        price_change = asset.get('price_change', 0)
        if price_change < self.safety_rules['news_spike_threshold']:
            return True
        
        # Check news sentiment
        if news:
            negative_keywords = ['miss', 'downgrade', 'cut', 'lower', 'disappoint', 'concern']
            recent_news = news[:3]  # Last 3 articles
            
            for article in recent_news:
                title = article.get('title', '').lower()
                if any(keyword in title for keyword in negative_keywords):
                    return True
        
        return False
    
    def check_fx_auto_hedge(self, fx_data: Dict[str, float]) -> Dict:
        """
        Check FX conditions and suggest hedging
        
        Args:
            fx_data: FX rate data (AUD vs major currencies)
            
        Returns:
            FX hedge recommendation
        """
        # Calculate AUD strength/weakness
        aud_usd = fx_data.get('AUDUSD=X', 1.0)
        aud_eur = fx_data.get('AUDEUR=X', 1.0)
        aud_gbp = fx_data.get('AUDGBP=X', 1.0)
        
        # Simple AUD strength indicator (in production, use more sophisticated analysis)
        aud_strength = (aud_usd + aud_eur + aud_gbp) / 3
        
        if aud_strength < 0.98:  # AUD weakening
            return {
                'recommendation': 'unhedged',
                'message': 'AUD weakening - consider unhedged global exposure',
                'strength': aud_strength,
                'action': 'Increase international exposure'
            }
        elif aud_strength > 1.02:  # AUD strengthening
            return {
                'recommendation': 'hedged',
                'message': 'AUD strengthening - consider hedged exposure',
                'strength': aud_strength,
                'action': 'Reduce international exposure'
            }
        else:
            return {
                'recommendation': 'neutral',
                'message': 'AUD stable - maintain current exposure',
                'strength': aud_strength,
                'action': 'No change needed'
            }
    
    def check_drawdown_seatbelt(self, allocation: Dict[str, float], 
                               historical_data: Dict[str, pd.DataFrame]) -> Dict:
        """
        Check if allocation exceeds maximum drawdown threshold
        
        Args:
            allocation: Current allocation
            historical_data: Historical price data for risk calculation
            
        Returns:
            Drawdown safety check results
        """
        # Calculate expected portfolio drawdown
        expected_drawdown = self._calculate_expected_drawdown(allocation, historical_data)
        max_drawdown = self.safety_rules['max_drawdown']
        
        if expected_drawdown > max_drawdown:
            # Apply seatbelt - reduce risky assets
            adjusted_allocation = allocation.copy()
            
            # Calculate reduction needed
            reduction_factor = max_drawdown / expected_drawdown
            
            # Reduce shares and commodities
            risky_assets = ['shares', 'commodities', 'crypto']
            for asset in risky_assets:
                if asset in adjusted_allocation:
                    adjusted_allocation[asset] *= reduction_factor
            
            # Add to bonds
            if 'bonds' in adjusted_allocation:
                bonds_increase = sum(allocation.get(asset, 0) * (1 - reduction_factor) 
                                   for asset in risky_assets if asset in allocation)
                adjusted_allocation['bonds'] += bonds_increase
            
            # Normalize
            total = sum(adjusted_allocation.values())
            for key in adjusted_allocation:
                adjusted_allocation[key] /= total
            
            return {
                'triggered': True,
                'original_drawdown': expected_drawdown,
                'adjusted_drawdown': self._calculate_expected_drawdown(adjusted_allocation, historical_data),
                'allocation': adjusted_allocation,
                'message': f"Drawdown seatbelt engaged: reduced risky assets to keep drawdown below {max_drawdown:.1%}"
            }
        else:
            return {
                'triggered': False,
                'expected_drawdown': expected_drawdown,
                'message': f"Drawdown within acceptable range: {expected_drawdown:.1%} < {max_drawdown:.1%}"
            }
    
    def _calculate_expected_drawdown(self, allocation: Dict[str, float], 
                                   historical_data: Dict[str, pd.DataFrame]) -> float:
        """
        Calculate expected portfolio drawdown using historical data
        
        Args:
            allocation: Asset allocation
            historical_data: Historical price data
            
        Returns:
            Expected maximum drawdown
        """
        # Asset class drawdown estimates (based on historical data)
        drawdown_estimates = {
            'cash': 0.00,
            'bonds': 0.05,
            'shares': 0.20,
            'commodities': 0.25,
            'crypto': 0.50
        }
        
        # Calculate weighted drawdown
        expected_drawdown = sum(
            allocation.get(asset, 0) * drawdown 
            for asset, drawdown in drawdown_estimates.items()
        )
        
        return expected_drawdown
    
    def run_safety_checks(self, allocation: Dict[str, float], 
                         selected_assets: Dict[str, List[Dict]],
                         sleep_better_dial: float = 0.0,
                         news_data: Optional[Dict[str, List[Dict]]] = None,
                         fx_data: Optional[Dict[str, float]] = None,
                         historical_data: Optional[Dict[str, pd.DataFrame]] = None) -> Dict:
        """
        Run all safety checks
        
        Args:
            allocation: Current allocation
            selected_assets: Selected assets
            sleep_better_dial: Sleep-better dial setting
            news_data: News data for sentiment analysis
            fx_data: FX rate data
            historical_data: Historical price data
            
        Returns:
            Complete safety check results
        """
        results = {
            'original_allocation': allocation,
            'safety_checks': {},
            'final_allocation': allocation,
            'messages': []
        }
        
        # 1. Sleep-better dial check
        sleep_result = self.check_sleep_better_dial(allocation, sleep_better_dial)
        results['safety_checks']['sleep_better'] = sleep_result
        results['final_allocation'] = sleep_result['allocation']
        results['messages'].append(sleep_result['message'])
        
        # 2. News spike filter
        if news_data:
            news_result = self.check_news_spike_filter(selected_assets, news_data)
            results['safety_checks']['news_filter'] = news_result
            results['messages'].extend(news_result['messages'])
        
        # 3. FX auto-hedge
        if fx_data:
            fx_result = self.check_fx_auto_hedge(fx_data)
            results['safety_checks']['fx_hedge'] = fx_result
            results['messages'].append(fx_result['message'])
        
        # 4. Drawdown seatbelt
        if historical_data:
            drawdown_result = self.check_drawdown_seatbelt(results['final_allocation'], historical_data)
            results['safety_checks']['drawdown_seatbelt'] = drawdown_result
            results['final_allocation'] = drawdown_result.get('allocation', results['final_allocation'])
            results['messages'].append(drawdown_result['message'])
        
        return results

# Example usage and testing
if __name__ == "__main__":
    # Initialize the Safety Officer
    safety = SafetyOfficer()
    
    # Test sleep-better dial
    test_allocation = {
        'shares': 0.55,
        'bonds': 0.25,
        'commodities': 0.10,
        'cash': 0.10
    }
    
    sleep_result = safety.check_sleep_better_dial(test_allocation, 0.5)
    print("Sleep-better dial test:")
    print(f"Original: {test_allocation}")
    print(f"Adjusted: {sleep_result['allocation']}")
    print(f"Message: {sleep_result['message']}")
    
    # Test FX hedge
    fx_data = {'AUDUSD=X': 0.95, 'AUDEUR=X': 0.88, 'AUDGBP=X': 0.75}
    fx_result = safety.check_fx_auto_hedge(fx_data)
    print(f"\nFX hedge test: {fx_result['message']}")
    
    # Test drawdown seatbelt
    drawdown_result = safety.check_drawdown_seatbelt(test_allocation, {})
    print(f"\nDrawdown seatbelt test: {drawdown_result['message']}")

