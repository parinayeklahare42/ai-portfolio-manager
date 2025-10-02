"""
The Selector - Asset selection engine
Picks the best assets within each class based on research scores
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class Selector:
    """
    The Selector picks the best assets within each class based on:
    - Research Crew analysis scores
    - Diversification requirements
    - Risk constraints
    """
    
    def __init__(self):
        # Selection rules for each asset class
        self.selection_rules = {
            'shares': {
                'max_assets': 2,
                'min_score': 0.3,
                'diversification': True,  # Avoid similar sectors
                'weight_split': [0.6, 0.4]  # 60/40 split for top 2
            },
            'bonds': {
                'max_assets': 1,
                'min_score': 0.4,
                'diversification': False,
                'weight_split': [1.0]
            },
            'commodities': {
                'max_assets': 1,
                'min_score': 0.3,
                'diversification': False,
                'weight_split': [1.0]
            },
            'crypto': {
                'max_assets': 1,
                'min_score': 0.2,
                'diversification': False,
                'weight_split': [1.0]
            }
        }
    
    def select_assets(self, asset_class: str, analysis_results: List[Dict], 
                    allocation_percentage: float) -> List[Dict]:
        """
        Select best assets for an asset class
        
        Args:
            asset_class: Asset class name
            analysis_results: Research Crew analysis results
            allocation_percentage: Target allocation for this class
            
        Returns:
            List of selected assets with weights
        """
        if not analysis_results:
            logger.warning(f"No analysis results for {asset_class}")
            return []
        
        # Get selection rules for this asset class
        rules = self.selection_rules.get(asset_class, {
            'max_assets': 1,
            'min_score': 0.3,
            'diversification': False,
            'weight_split': [1.0]
        })
        
        # Filter by minimum score
        qualified_assets = [
            asset for asset in analysis_results 
            if asset.get('composite_score', 0) >= rules['min_score']
        ]
        
        if not qualified_assets:
            logger.warning(f"No qualified assets for {asset_class}")
            return []
        
        # Select top assets
        max_assets = min(rules['max_assets'], len(qualified_assets))
        selected_assets = qualified_assets[:max_assets]
        
        # Apply diversification if required
        if rules['diversification'] and asset_class == 'shares':
            selected_assets = self._apply_diversification(selected_assets)
        
        # Assign weights
        weight_split = rules['weight_split'][:len(selected_assets)]
        total_weight = sum(weight_split)
        
        for i, asset in enumerate(selected_assets):
            if i < len(weight_split):
                asset['weight'] = weight_split[i] / total_weight
                asset['allocation_percentage'] = allocation_percentage * asset['weight']
            else:
                asset['weight'] = 0.0
                asset['allocation_percentage'] = 0.0
        
        logger.info(f"Selected {len(selected_assets)} {asset_class} assets")
        return selected_assets
    
    def _apply_diversification(self, assets: List[Dict]) -> List[Dict]:
        """
        Apply diversification rules to avoid similar assets
        
        Args:
            assets: List of assets sorted by score
            
        Returns:
            Diversified list of assets
        """
        if len(assets) <= 1:
            return assets
        
        # Simple diversification: avoid assets with similar tickers
        # In a real system, you'd use sector classification
        diversified = [assets[0]]  # Always include the best
        
        for asset in assets[1:]:
            # Check if this asset is too similar to already selected ones
            is_diverse = True
            for selected in diversified:
                if self._are_similar_assets(asset['ticker'], selected['ticker']):
                    is_diverse = False
                    break
            
            if is_diverse:
                diversified.append(asset)
                if len(diversified) >= 2:  # Max 2 for shares
                    break
        
        return diversified
    
    def _are_similar_assets(self, ticker1: str, ticker2: str) -> bool:
        """
        Check if two assets are too similar (same sector/company)
        
        Args:
            ticker1: First ticker
            ticker2: Second ticker
            
        Returns:
            True if assets are similar
        """
        # Simple similarity check based on ticker patterns
        # In production, you'd use proper sector classification
        
        # Same company different share classes
        if ticker1.split('.')[0] == ticker2.split('.')[0]:
            return True
        
        # Both banks (CBA, WBC, ANZ, NAB)
        bank_tickers = ['CBA', 'WBC', 'ANZ', 'NAB']
        if (ticker1.split('.')[0] in bank_tickers and 
            ticker2.split('.')[0] in bank_tickers):
            return True
        
        # Both miners (BHP, RIO, FMG)
        miner_tickers = ['BHP', 'RIO', 'FMG']
        if (ticker1.split('.')[0] in miner_tickers and 
            ticker2.split('.')[0] in miner_tickers):
            return True
        
        return False
    
    def create_portfolio_selection(self, analysis_results: Dict[str, List[Dict]], 
                                 allocation: Dict[str, float]) -> Dict[str, List[Dict]]:
        """
        Create complete portfolio selection
        
        Args:
            analysis_results: Research results by asset class
            allocation: Target allocation percentages
            
        Returns:
            Selected assets for each class
        """
        portfolio_selection = {}
        
        for asset_class, percentage in allocation.items():
            if percentage > 0 and asset_class in analysis_results:
                selected = self.select_assets(
                    asset_class, 
                    analysis_results[asset_class], 
                    percentage
                )
                portfolio_selection[asset_class] = selected
            else:
                portfolio_selection[asset_class] = []
        
        # Log summary
        total_assets = sum(len(assets) for assets in portfolio_selection.values())
        logger.info(f"Portfolio selection complete: {total_assets} assets selected")
        
        return portfolio_selection
    
    def get_selection_summary(self, portfolio_selection: Dict[str, List[Dict]]) -> Dict:
        """
        Get summary of portfolio selection
        
        Args:
            portfolio_selection: Selected assets by class
            
        Returns:
            Summary statistics
        """
        summary = {
            'total_assets': 0,
            'by_class': {},
            'total_allocation': 0.0,
            'avg_score': 0.0
        }
        
        all_scores = []
        
        for asset_class, assets in portfolio_selection.items():
            class_summary = {
                'count': len(assets),
                'allocation': sum(asset.get('allocation_percentage', 0) for asset in assets),
                'avg_score': np.mean([asset.get('composite_score', 0) for asset in assets]) if assets else 0
            }
            
            summary['by_class'][asset_class] = class_summary
            summary['total_assets'] += len(assets)
            summary['total_allocation'] += class_summary['allocation']
            
            all_scores.extend([asset.get('composite_score', 0) for asset in assets])
        
        summary['avg_score'] = np.mean(all_scores) if all_scores else 0
        
        return summary
    
    def create_buy_list(self, portfolio_selection: Dict[str, List[Dict]], 
                       total_budget: float) -> List[Dict]:
        """
        Create final buy list with dollar amounts
        
        Args:
            portfolio_selection: Selected assets
            total_budget: Total investment amount
            
        Returns:
            List of buy orders
        """
        buy_list = []
        
        for asset_class, assets in portfolio_selection.items():
            for asset in assets:
                if asset.get('allocation_percentage', 0) > 0:
                    dollar_amount = total_budget * asset['allocation_percentage']
                    current_price = asset.get('current_price', 0)
                    
                    if current_price > 0:
                        shares = int(dollar_amount / current_price)
                        actual_cost = shares * current_price
                        leftover = dollar_amount - actual_cost
                        
                        buy_order = {
                            'ticker': asset['ticker'],
                            'asset_class': asset_class,
                            'current_price': current_price,
                            'shares': shares,
                            'dollar_amount': dollar_amount,
                            'actual_cost': actual_cost,
                            'leftover': leftover,
                            'weight': asset['weight'],
                            'allocation_percentage': asset['allocation_percentage'],
                            'composite_score': asset.get('composite_score', 0)
                        }
                        
                        buy_list.append(buy_order)
        
        # Sort by allocation percentage (highest first)
        buy_list.sort(key=lambda x: x['allocation_percentage'], reverse=True)
        
        return buy_list

# Example usage and testing
if __name__ == "__main__":
    # Initialize the Selector
    selector = Selector()
    
    # Create sample analysis results
    sample_analysis = {
        'shares': [
            {'ticker': 'CBA.AX', 'composite_score': 0.85, 'current_price': 95.50},
            {'ticker': 'BHP.AX', 'composite_score': 0.78, 'current_price': 45.20},
            {'ticker': 'WBC.AX', 'composite_score': 0.72, 'current_price': 22.10},
            {'ticker': 'RIO.AX', 'composite_score': 0.68, 'current_price': 120.30}
        ],
        'bonds': [
            {'ticker': 'VGB.AX', 'composite_score': 0.75, 'current_price': 105.20}
        ],
        'commodities': [
            {'ticker': 'GOLD.AX', 'composite_score': 0.65, 'current_price': 25.80}
        ]
    }
    
    # Sample allocation
    allocation = {
        'shares': 0.55,
        'bonds': 0.25,
        'commodities': 0.10,
        'cash': 0.10
    }
    
    # Create portfolio selection
    selection = selector.create_portfolio_selection(sample_analysis, allocation)
    
    # Create buy list
    buy_list = selector.create_buy_list(selection, 2500)
    
    print("Portfolio Selection:")
    for asset_class, assets in selection.items():
        print(f"\n{asset_class.upper()}:")
        for asset in assets:
            print(f"  {asset['ticker']}: {asset['allocation_percentage']:.1%} (score: {asset.get('composite_score', 0):.3f})")
    
    print(f"\nBuy List (Total Budget: $2,500):")
    for order in buy_list:
        print(f"{order['ticker']}: {order['shares']} shares @ ${order['current_price']:.2f} = ${order['actual_cost']:.2f}")

