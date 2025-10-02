"""
The Shopkeeper - Portfolio execution engine
Converts allocation percentages to actual trades and dollar amounts
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Shopkeeper:
    """
    The Shopkeeper handles:
    1. Converting percentages to dollar amounts
    2. Calculating whole share quantities
    3. Managing leftover cash
    4. Creating executable trade orders
    """
    
    def __init__(self):
        self.min_trade_size = 50  # Minimum trade size in dollars
        self.rounding_precision = 2  # Decimal places for dollar amounts
    
    def calculate_dollar_amounts(self, allocation: Dict[str, float], 
                               total_budget: float) -> Dict[str, float]:
        """
        Convert allocation percentages to dollar amounts
        
        Args:
            allocation: Asset allocation percentages
            total_budget: Total investment budget
            
        Returns:
            Dollar amounts for each asset class
        """
        dollar_amounts = {}
        
        for asset_class, percentage in allocation.items():
            dollar_amount = total_budget * percentage
            dollar_amounts[asset_class] = round(dollar_amount, self.rounding_precision)
        
        return dollar_amounts
    
    def calculate_share_quantities(self, selected_assets: Dict[str, List[Dict]], 
                                 dollar_amounts: Dict[str, float]) -> List[Dict]:
        """
        Calculate share quantities for each selected asset
        
        Args:
            selected_assets: Selected assets by class
            dollar_amounts: Dollar amounts by class
            
        Returns:
            List of trade orders with share quantities
        """
        trade_orders = []
        
        for asset_class, assets in selected_assets.items():
            class_budget = dollar_amounts.get(asset_class, 0)
            
            for asset in assets:
                ticker = asset['ticker']
                current_price = asset.get('current_price', 0)
                weight = asset.get('weight', 0)
                
                if current_price > 0 and weight > 0:
                    # Calculate dollar amount for this asset
                    asset_dollar_amount = class_budget * weight
                    
                    # Calculate share quantity (whole shares only)
                    shares = int(asset_dollar_amount / current_price)
                    actual_cost = shares * current_price
                    leftover = asset_dollar_amount - actual_cost
                    
                    # Only include if meets minimum trade size
                    if actual_cost >= self.min_trade_size:
                        trade_order = {
                            'ticker': ticker,
                            'asset_class': asset_class,
                            'current_price': current_price,
                            'target_amount': asset_dollar_amount,
                            'shares': shares,
                            'actual_cost': actual_cost,
                            'leftover': leftover,
                            'weight': weight,
                            'allocation_percentage': asset.get('allocation_percentage', 0),
                            'composite_score': asset.get('composite_score', 0)
                        }
                        
                        trade_orders.append(trade_order)
                    else:
                        logger.info(f"Skipping {ticker}: trade size ${actual_cost:.2f} below minimum ${self.min_trade_size}")
        
        return trade_orders
    
    def optimize_leftover_cash(self, trade_orders: List[Dict], 
                              total_budget: float) -> List[Dict]:
        """
        Optimize leftover cash by suggesting additional shares
        
        Args:
            trade_orders: Current trade orders
            total_budget: Total budget
            
        Returns:
            Optimized trade orders with leftover cash suggestions
        """
        # Calculate total spent and leftover
        total_spent = sum(order['actual_cost'] for order in trade_orders)
        total_leftover = total_budget - total_spent
        
        if total_leftover < self.min_trade_size:
            return trade_orders
        
        # Find the best asset to buy more of (highest score)
        best_order = max(trade_orders, key=lambda x: x['composite_score'])
        
        # Calculate how many more shares we can buy
        additional_shares = int(total_leftover / best_order['current_price'])
        
        if additional_shares > 0:
            additional_cost = additional_shares * best_order['current_price']
            best_order['shares'] += additional_shares
            best_order['actual_cost'] += additional_cost
            best_order['leftover'] = total_leftover - additional_cost
            
            logger.info(f"Optimized: added {additional_shares} shares of {best_order['ticker']}")
        
        return trade_orders
    
    def create_buy_list(self, trade_orders: List[Dict], 
                       total_budget: float) -> Dict:
        """
        Create final buy list with summary
        
        Args:
            trade_orders: Trade orders
            total_budget: Total budget
            
        Returns:
            Complete buy list with summary
        """
        # Sort by allocation percentage (highest first)
        trade_orders.sort(key=lambda x: x['allocation_percentage'], reverse=True)
        
        # Calculate summary statistics
        total_spent = sum(order['actual_cost'] for order in trade_orders)
        total_leftover = total_budget - total_spent
        total_shares = sum(order['shares'] for order in trade_orders)
        
        # Group by asset class
        by_class = {}
        for order in trade_orders:
            asset_class = order['asset_class']
            if asset_class not in by_class:
                by_class[asset_class] = []
            by_class[asset_class].append(order)
        
        return {
            'trade_orders': trade_orders,
            'summary': {
                'total_budget': total_budget,
                'total_spent': total_spent,
                'total_leftover': total_leftover,
                'total_shares': total_shares,
                'num_assets': len(trade_orders),
                'by_class': by_class
            },
            'created_at': datetime.now().isoformat()
        }
    
    def create_rebalance_orders(self, current_portfolio: Dict[str, float], 
                              target_allocation: Dict[str, float], 
                              portfolio_value: float) -> List[Dict]:
        """
        Create rebalancing orders
        
        Args:
            current_portfolio: Current portfolio allocation
            target_allocation: Target allocation
            portfolio_value: Current portfolio value
            
        Returns:
            List of rebalancing orders
        """
        rebalance_orders = []
        
        for asset_class in target_allocation:
            current_weight = current_portfolio.get(asset_class, 0)
            target_weight = target_allocation[asset_class]
            weight_diff = target_weight - current_weight
            
            if abs(weight_diff) > 0.01:  # Only rebalance if difference > 1%
                dollar_diff = weight_diff * portfolio_value
                
                if dollar_diff > 0:
                    action = 'BUY'
                else:
                    action = 'SELL'
                    dollar_diff = abs(dollar_diff)
                
                rebalance_orders.append({
                    'asset_class': asset_class,
                    'action': action,
                    'current_weight': current_weight,
                    'target_weight': target_weight,
                    'weight_diff': weight_diff,
                    'dollar_amount': dollar_diff
                })
        
        return rebalance_orders
    
    def format_buy_list(self, buy_list: Dict) -> str:
        """
        Format buy list for display
        
        Args:
            buy_list: Buy list dictionary
            
        Returns:
            Formatted string
        """
        output = []
        output.append("=" * 60)
        output.append("PORTFOLIO BUY LIST")
        output.append("=" * 60)
        
        # Summary
        summary = buy_list['summary']
        output.append(f"Total Budget: ${summary['total_budget']:,.2f}")
        output.append(f"Total Spent: ${summary['total_spent']:,.2f}")
        output.append(f"Leftover Cash: ${summary['total_leftover']:,.2f}")
        output.append(f"Total Shares: {summary['total_shares']:,}")
        output.append("")
        
        # Trade orders
        output.append("TRADE ORDERS:")
        output.append("-" * 60)
        output.append(f"{'Ticker':<12} {'Price':<8} {'Shares':<8} {'Cost':<12} {'%':<6}")
        output.append("-" * 60)
        
        for order in buy_list['trade_orders']:
            percentage = order['allocation_percentage'] * 100
            output.append(
                f"{order['ticker']:<12} "
                f"${order['current_price']:<7.2f} "
                f"{order['shares']:<8} "
                f"${order['actual_cost']:<11.2f} "
                f"{percentage:<5.1f}%"
            )
        
        output.append("")
        output.append("=" * 60)
        
        return "\n".join(output)
    
    def create_execution_summary(self, buy_list: Dict) -> Dict:
        """
        Create execution summary for portfolio management
        
        Args:
            buy_list: Buy list dictionary
            
        Returns:
            Execution summary
        """
        summary = buy_list['summary']
        
        # Calculate efficiency metrics
        execution_efficiency = (summary['total_spent'] / summary['total_budget']) * 100
        leftover_percentage = (summary['total_leftover'] / summary['total_budget']) * 100
        
        # Asset class breakdown
        class_breakdown = {}
        for asset_class, orders in summary['by_class'].items():
            class_total = sum(order['actual_cost'] for order in orders)
            class_breakdown[asset_class] = {
                'amount': class_total,
                'percentage': (class_total / summary['total_spent']) * 100 if summary['total_spent'] > 0 else 0,
                'num_assets': len(orders)
            }
        
        return {
            'execution_efficiency': execution_efficiency,
            'leftover_percentage': leftover_percentage,
            'class_breakdown': class_breakdown,
            'total_assets': summary['num_assets'],
            'avg_trade_size': summary['total_spent'] / summary['num_assets'] if summary['num_assets'] > 0 else 0,
            'created_at': buy_list['created_at']
        }

# Example usage and testing
if __name__ == "__main__":
    # Initialize the Shopkeeper
    shopkeeper = Shopkeeper()
    
    # Test data
    test_allocation = {
        'shares': 0.55,
        'bonds': 0.25,
        'commodities': 0.10,
        'cash': 0.10
    }
    
    test_assets = {
        'shares': [
            {'ticker': 'CBA.AX', 'current_price': 95.50, 'weight': 0.6, 'allocation_percentage': 0.33, 'composite_score': 0.85},
            {'ticker': 'BHP.AX', 'current_price': 45.20, 'weight': 0.4, 'allocation_percentage': 0.22, 'composite_score': 0.78}
        ],
        'bonds': [
            {'ticker': 'VGB.AX', 'current_price': 105.20, 'weight': 1.0, 'allocation_percentage': 0.25, 'composite_score': 0.75}
        ],
        'commodities': [
            {'ticker': 'GOLD.AX', 'current_price': 25.80, 'weight': 1.0, 'allocation_percentage': 0.10, 'composite_score': 0.65}
        ]
    }
    
    # Calculate dollar amounts
    dollar_amounts = shopkeeper.calculate_dollar_amounts(test_allocation, 2500)
    print("Dollar amounts:", dollar_amounts)
    
    # Calculate share quantities
    trade_orders = shopkeeper.calculate_share_quantities(test_assets, dollar_amounts)
    print(f"\nTrade orders: {len(trade_orders)}")
    
    # Create buy list
    buy_list = shopkeeper.create_buy_list(trade_orders, 2500)
    
    # Format and display
    formatted = shopkeeper.format_buy_list(buy_list)
    print(f"\n{formatted}")
    
    # Execution summary
    summary = shopkeeper.create_execution_summary(buy_list)
    print(f"\nExecution Summary:")
    print(f"Efficiency: {summary['execution_efficiency']:.1f}%")
    print(f"Leftover: {summary['leftover_percentage']:.1f}%")
    print(f"Total Assets: {summary['total_assets']}")

