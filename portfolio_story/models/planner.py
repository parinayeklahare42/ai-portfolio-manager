"""
The Planner - Asset allocation system
Creates base portfolio allocation based on time horizon and risk preferences
"""

import numpy as np
from typing import Dict, List, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TimeHorizon(Enum):
    SHORT_TERM = "short_term"  # < 2 years
    MEDIUM_TERM = "medium_term"  # 2-5 years
    LONG_TERM = "long_term"  # > 5 years

class RiskProfile(Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

class Planner:
    """
    The Planner creates base asset allocation based on:
    - Time horizon (short/medium/long term)
    - Risk profile (conservative/moderate/aggressive)
    - Sleep-better dial (additional risk adjustment)
    """
    
    def __init__(self):
        # Base allocation templates
        self.allocation_templates = {
            TimeHorizon.SHORT_TERM: {
                'cash': 0.40,
                'bonds': 0.45,
                'shares': 0.10,
                'commodities': 0.05,
                'crypto': 0.00
            },
            TimeHorizon.MEDIUM_TERM: {
                'cash': 0.20,
                'bonds': 0.40,
                'shares': 0.30,
                'commodities': 0.08,
                'crypto': 0.02
            },
            TimeHorizon.LONG_TERM: {
                'cash': 0.05,
                'bonds': 0.25,
                'shares': 0.55,
                'commodities': 0.10,
                'crypto': 0.05
            }
        }
        
        # Risk profile adjustments
        self.risk_adjustments = {
            RiskProfile.CONSERVATIVE: {
                'shares': -0.10,
                'bonds': 0.10,
                'cash': 0.00
            },
            RiskProfile.MODERATE: {
                'shares': 0.00,
                'bonds': 0.00,
                'cash': 0.00
            },
            RiskProfile.AGGRESSIVE: {
                'shares': 0.10,
                'bonds': -0.10,
                'cash': 0.00
            }
        }
    
    def create_base_allocation(self, time_horizon: str, risk_profile: str = "moderate") -> Dict[str, float]:
        """
        Create base allocation based on time horizon and risk profile
        
        Args:
            time_horizon: 'short_term', 'medium_term', or 'long_term'
            risk_profile: 'conservative', 'moderate', or 'aggressive'
            
        Returns:
            Dictionary with asset class allocations
        """
        try:
            # Convert string inputs to enums
            horizon_enum = TimeHorizon(time_horizon)
            risk_enum = RiskProfile(risk_profile)
            
            # Get base allocation
            base_allocation = self.allocation_templates[horizon_enum].copy()
            
            # Apply risk profile adjustments
            risk_adj = self.risk_adjustments[risk_enum]
            for asset_class, adjustment in risk_adj.items():
                if asset_class in base_allocation:
                    base_allocation[asset_class] += adjustment
            
            # Ensure allocations sum to 1.0 and are non-negative
            base_allocation = self._normalize_allocation(base_allocation)
            
            logger.info(f"Created base allocation for {time_horizon} {risk_profile}")
            return base_allocation
            
        except ValueError as e:
            logger.error(f"Invalid input parameters: {e}")
            # Return moderate long-term allocation as default
            return self.allocation_templates[TimeHorizon.LONG_TERM].copy()
    
    def apply_sleep_better_dial(self, allocation: Dict[str, float], 
                              sleep_better_dial: float) -> Dict[str, float]:
        """
        Apply sleep-better dial adjustment (0-1 scale)
        
        Args:
            allocation: Current allocation
            sleep_better_dial: 0 (aggressive) to 1 (conservative)
            
        Returns:
            Adjusted allocation
        """
        # Calculate adjustment amount
        # At 0 (aggressive): no change
        # At 1 (conservative): move 20% from shares to bonds
        max_adjustment = 0.20
        adjustment = sleep_better_dial * max_adjustment
        
        # Apply adjustment
        adjusted_allocation = allocation.copy()
        
        if 'shares' in adjusted_allocation and 'bonds' in adjusted_allocation:
            # Move from shares to bonds
            shares_reduction = min(adjustment, adjusted_allocation['shares'])
            adjusted_allocation['shares'] -= shares_reduction
            adjusted_allocation['bonds'] += shares_reduction
        
        # Re-normalize
        adjusted_allocation = self._normalize_allocation(adjusted_allocation)
        
        logger.info(f"Applied sleep-better dial: {sleep_better_dial:.2f} (adjustment: {adjustment:.2f})")
        return adjusted_allocation
    
    def apply_risk_budget(self, allocation: Dict[str, float], 
                         target_volatility: float) -> Dict[str, float]:
        """
        Adjust allocation to meet target volatility
        
        Args:
            allocation: Current allocation
            target_volatility: Target portfolio volatility (e.g., 0.10 for 10%)
            
        Returns:
            Risk-adjusted allocation
        """
        # Asset class volatility estimates (annualized)
        volatility_estimates = {
            'cash': 0.02,
            'bonds': 0.05,
            'shares': 0.20,
            'commodities': 0.25,
            'crypto': 0.60
        }
        
        # Calculate current portfolio volatility
        current_vol = sum(allocation.get(asset, 0) * vol for asset, vol in volatility_estimates.items())
        
        # If current volatility is too high, reduce risky assets
        if current_vol > target_volatility:
            reduction_factor = target_volatility / current_vol
            
            # Apply reduction to risky assets (shares, commodities, crypto)
            risky_assets = ['shares', 'commodities', 'crypto']
            total_risky = sum(allocation.get(asset, 0) for asset in risky_assets)
            
            if total_risky > 0:
                # Calculate how much to move to safer assets
                risky_reduction = total_risky * (1 - reduction_factor)
                
                # Reduce risky assets proportionally
                for asset in risky_assets:
                    if asset in allocation:
                        reduction = allocation[asset] * (risky_reduction / total_risky)
                        allocation[asset] = max(0, allocation[asset] - reduction)
                
                # Add to bonds
                if 'bonds' in allocation:
                    allocation['bonds'] += risky_reduction
        
        # Re-normalize
        allocation = self._normalize_allocation(allocation)
        
        logger.info(f"Applied risk budget: target vol {target_volatility:.2f}")
        return allocation
    
    def _normalize_allocation(self, allocation: Dict[str, float]) -> Dict[str, float]:
        """
        Ensure allocation sums to 1.0 and all values are non-negative
        
        Args:
            allocation: Allocation dictionary
            
        Returns:
            Normalized allocation
        """
        # Ensure non-negative values
        for key in allocation:
            allocation[key] = max(0.0, allocation[key])
        
        # Calculate total
        total = sum(allocation.values())
        
        # Normalize if total > 0
        if total > 0:
            for key in allocation:
                allocation[key] /= total
        else:
            # If all zeros, set equal allocation
            num_assets = len(allocation)
            for key in allocation:
                allocation[key] = 1.0 / num_assets
        
        return allocation
    
    def create_portfolio_plan(self, time_horizon: str, risk_profile: str = "moderate",
                            sleep_better_dial: float = 0.0, target_volatility: float = 0.10) -> Dict:
        """
        Create complete portfolio plan
        
        Args:
            time_horizon: Investment time horizon
            risk_profile: Risk tolerance
            sleep_better_dial: Additional risk adjustment (0-1)
            target_volatility: Target portfolio volatility
            
        Returns:
            Complete portfolio plan
        """
        # Create base allocation
        allocation = self.create_base_allocation(time_horizon, risk_profile)
        
        # Apply sleep-better dial
        allocation = self.apply_sleep_better_dial(allocation, sleep_better_dial)
        
        # Apply risk budget
        allocation = self.apply_risk_budget(allocation, target_volatility)
        
        # Calculate expected metrics
        expected_volatility = self._calculate_expected_volatility(allocation)
        expected_return = self._calculate_expected_return(allocation)
        
        return {
            'allocation': allocation,
            'time_horizon': time_horizon,
            'risk_profile': risk_profile,
            'sleep_better_dial': sleep_better_dial,
            'target_volatility': target_volatility,
            'expected_volatility': expected_volatility,
            'expected_return': expected_return,
            'plan_date': np.datetime64('now').astype(str)
        }
    
    def _calculate_expected_volatility(self, allocation: Dict[str, float]) -> float:
        """Calculate expected portfolio volatility"""
        volatility_estimates = {
            'cash': 0.02,
            'bonds': 0.05,
            'shares': 0.20,
            'commodities': 0.25,
            'crypto': 0.60
        }
        
        return sum(allocation.get(asset, 0) * vol for asset, vol in volatility_estimates.items())
    
    def _calculate_expected_return(self, allocation: Dict[str, float]) -> float:
        """Calculate expected portfolio return"""
        return_estimates = {
            'cash': 0.03,
            'bonds': 0.04,
            'shares': 0.08,
            'commodities': 0.06,
            'crypto': 0.12
        }
        
        return sum(allocation.get(asset, 0) * ret for asset, ret in return_estimates.items())

# Example usage and testing
if __name__ == "__main__":
    # Initialize the Planner
    planner = Planner()
    
    # Test different scenarios
    scenarios = [
        ("long_term", "moderate", 0.0, 0.10),
        ("long_term", "conservative", 0.5, 0.08),
        ("short_term", "aggressive", 0.2, 0.12),
        ("medium_term", "moderate", 0.8, 0.09)
    ]
    
    for time_horizon, risk_profile, sleep_dial, target_vol in scenarios:
        plan = planner.create_portfolio_plan(time_horizon, risk_profile, sleep_dial, target_vol)
        
        print(f"\nScenario: {time_horizon}, {risk_profile}, sleep_dial={sleep_dial}")
        print(f"Allocation: {plan['allocation']}")
        print(f"Expected Volatility: {plan['expected_volatility']:.3f}")
        print(f"Expected Return: {plan['expected_return']:.3f}")

