"""
The Caretaker - Portfolio rebalancing system
Monitors portfolio drift and triggers rebalancing when needed
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class Caretaker:
    """
    The Caretaker handles:
    1. Portfolio drift monitoring
    2. Threshold-based rebalancing
    3. Minimum trade size filtering
    4. Turnover management
    """
    
    def __init__(self):
        self.default_drift_threshold = 0.05  # 5% drift threshold
        self.min_trade_size = 100  # Minimum trade size in dollars
        self.max_turnover = 0.20  # Maximum 20% turnover per rebalance
        self.rebalance_frequency = 30  # Days between rebalances
    
    def calculate_portfolio_drift(self, current_allocation: Dict[str, float], 
                                target_allocation: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate drift for each asset class
        
        Args:
            current_allocation: Current portfolio allocation
            target_allocation: Target allocation
            
        Returns:
            Drift percentages for each asset class
        """
        drift = {}
        
        for asset_class in target_allocation:
            current_weight = current_allocation.get(asset_class, 0)
            target_weight = target_allocation[asset_class]
            drift[asset_class] = current_weight - target_weight
        
        return drift
    
    def check_drift_threshold(self, drift: Dict[str, float], 
                            threshold: float = None) -> Dict[str, bool]:
        """
        Check if any asset class exceeds drift threshold
        
        Args:
            drift: Drift percentages
            threshold: Drift threshold (default from config)
            
        Returns:
            Dictionary of threshold violations
        """
        if threshold is None:
            threshold = self.default_drift_threshold
        
        violations = {}
        for asset_class, drift_value in drift.items():
            violations[asset_class] = abs(drift_value) > threshold
        
        return violations
    
    def calculate_rebalance_trades(self, current_allocation: Dict[str, float], 
                                 target_allocation: Dict[str, float], 
                                 portfolio_value: float) -> List[Dict]:
        """
        Calculate rebalancing trades needed
        
        Args:
            current_allocation: Current allocation
            target_allocation: Target allocation
            portfolio_value: Current portfolio value
            
        Returns:
            List of rebalancing trades
        """
        trades = []
        
        for asset_class in target_allocation:
            current_weight = current_allocation.get(asset_class, 0)
            target_weight = target_allocation[asset_class]
            weight_diff = target_weight - current_weight
            
            if abs(weight_diff) > 0.001:  # Only if meaningful difference
                dollar_amount = weight_diff * portfolio_value
                
                if abs(dollar_amount) >= self.min_trade_size:
                    trade = {
                        'asset_class': asset_class,
                        'current_weight': current_weight,
                        'target_weight': target_weight,
                        'weight_diff': weight_diff,
                        'dollar_amount': dollar_amount,
                        'action': 'BUY' if dollar_amount > 0 else 'SELL',
                        'trade_size': abs(dollar_amount)
                    }
                    trades.append(trade)
        
        return trades
    
    def check_turnover_limit(self, trades: List[Dict], 
                           portfolio_value: float) -> bool:
        """
        Check if rebalancing trades exceed turnover limit
        
        Args:
            trades: List of rebalancing trades
            portfolio_value: Portfolio value
            
        Returns:
            True if within turnover limit
        """
        total_turnover = sum(trade['trade_size'] for trade in trades)
        turnover_percentage = total_turnover / portfolio_value
        
        return turnover_percentage <= self.max_turnover
    
    def filter_trades_by_size(self, trades: List[Dict]) -> List[Dict]:
        """
        Filter out trades below minimum size
        
        Args:
            trades: List of trades
            
        Returns:
            Filtered trades
        """
        return [trade for trade in trades if trade['trade_size'] >= self.min_trade_size]
    
    def prioritize_trades(self, trades: List[Dict]) -> List[Dict]:
        """
        Prioritize trades by size and importance
        
        Args:
            trades: List of trades
            
        Returns:
            Prioritized trades
        """
        # Sort by trade size (largest first)
        return sorted(trades, key=lambda x: x['trade_size'], reverse=True)
    
    def create_rebalance_plan(self, current_allocation: Dict[str, float], 
                            target_allocation: Dict[str, float], 
                            portfolio_value: float,
                            drift_threshold: float = None) -> Dict:
        """
        Create complete rebalancing plan
        
        Args:
            current_allocation: Current allocation
            target_allocation: Target allocation
            portfolio_value: Portfolio value
            drift_threshold: Drift threshold
            
        Returns:
            Complete rebalancing plan
        """
        # Calculate drift
        drift = self.calculate_portfolio_drift(current_allocation, target_allocation)
        
        # Check threshold violations
        violations = self.check_drift_threshold(drift, drift_threshold)
        
        # Calculate trades
        trades = self.calculate_rebalance_trades(current_allocation, target_allocation, portfolio_value)
        
        # Filter by size
        filtered_trades = self.filter_trades_by_size(trades)
        
        # Check turnover limit
        within_turnover_limit = self.check_turnover_limit(filtered_trades, portfolio_value)
        
        # Prioritize trades
        prioritized_trades = self.prioritize_trades(filtered_trades)
        
        # Calculate summary metrics
        total_turnover = sum(trade['trade_size'] for trade in prioritized_trades)
        turnover_percentage = total_turnover / portfolio_value if portfolio_value > 0 else 0
        
        return {
            'drift': drift,
            'violations': violations,
            'trades': prioritized_trades,
            'within_turnover_limit': within_turnover_limit,
            'total_turnover': total_turnover,
            'turnover_percentage': turnover_percentage,
            'num_trades': len(prioritized_trades),
            'action_needed': any(violations.values()),
            'created_at': datetime.now().isoformat()
        }
    
    def should_rebalance(self, current_allocation: Dict[str, float], 
                        target_allocation: Dict[str, float],
                        last_rebalance_date: Optional[datetime] = None) -> bool:
        """
        Determine if portfolio should be rebalanced
        
        Args:
            current_allocation: Current allocation
            target_allocation: Target allocation
            last_rebalance_date: Date of last rebalance
            
        Returns:
            True if rebalancing is needed
        """
        # Check time since last rebalance
        if last_rebalance_date:
            days_since_rebalance = (datetime.now() - last_rebalance_date).days
            if days_since_rebalance < self.rebalance_frequency:
                return False
        
        # Check drift threshold
        drift = self.calculate_portfolio_drift(current_allocation, target_allocation)
        violations = self.check_drift_threshold(drift)
        
        return any(violations.values())
    
    def create_rebalance_summary(self, rebalance_plan: Dict) -> str:
        """
        Create human-readable rebalancing summary
        
        Args:
            rebalance_plan: Rebalancing plan
            
        Returns:
            Formatted summary string
        """
        if not rebalance_plan['action_needed']:
            return "No rebalancing needed - portfolio within target allocation"
        
        summary = []
        summary.append("REBALANCING REQUIRED")
        summary.append("=" * 40)
        
        # Show drift
        summary.append("Current Drift:")
        for asset_class, drift in rebalance_plan['drift'].items():
            if abs(drift) > 0.01:  # Only show meaningful drift
                summary.append(f"  {asset_class}: {drift:+.1%}")
        
        summary.append("")
        
        # Show trades
        if rebalance_plan['trades']:
            summary.append("Required Trades:")
            for trade in rebalance_plan['trades']:
                action = trade['action']
                amount = trade['dollar_amount']
                summary.append(f"  {action} {trade['asset_class']}: ${amount:,.2f}")
        else:
            summary.append("No trades needed (below minimum size)")
        
        summary.append("")
        summary.append(f"Total Turnover: {rebalance_plan['turnover_percentage']:.1%}")
        summary.append(f"Number of Trades: {rebalance_plan['num_trades']}")
        
        return "\n".join(summary)
    
    def simulate_rebalance(self, current_allocation: Dict[str, float], 
                          trades: List[Dict]) -> Dict[str, float]:
        """
        Simulate the effect of rebalancing trades
        
        Args:
            current_allocation: Current allocation
            trades: Rebalancing trades
            
        Returns:
            New allocation after trades
        """
        new_allocation = current_allocation.copy()
        
        for trade in trades:
            asset_class = trade['asset_class']
            weight_change = trade['weight_diff']
            new_allocation[asset_class] = new_allocation.get(asset_class, 0) + weight_change
        
        # Normalize to ensure weights sum to 1
        total = sum(new_allocation.values())
        if total > 0:
            for key in new_allocation:
                new_allocation[key] /= total
        
        return new_allocation

# Example usage and testing
if __name__ == "__main__":
    # Initialize the Caretaker
    caretaker = Caretaker()
    
    # Test data
    current_allocation = {
        'shares': 0.60,  # Drifted up from 0.55
        'bonds': 0.20,   # Drifted down from 0.25
        'commodities': 0.12,  # Drifted up from 0.10
        'cash': 0.08     # Drifted down from 0.10
    }
    
    target_allocation = {
        'shares': 0.55,
        'bonds': 0.25,
        'commodities': 0.10,
        'cash': 0.10
    }
    
    portfolio_value = 2500
    
    # Create rebalance plan
    plan = caretaker.create_rebalance_plan(current_allocation, target_allocation, portfolio_value)
    
    # Display results
    print("Rebalancing Plan:")
    print(f"Action needed: {plan['action_needed']}")
    print(f"Total turnover: {plan['turnover_percentage']:.1%}")
    print(f"Number of trades: {plan['num_trades']}")
    
    # Show summary
    summary = caretaker.create_rebalance_summary(plan)
    print(f"\n{summary}")
    
    # Simulate rebalance
    new_allocation = caretaker.simulate_rebalance(current_allocation, plan['trades'])
    print(f"\nNew allocation after rebalance: {new_allocation}")

