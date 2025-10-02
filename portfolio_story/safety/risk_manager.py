"""
The Risk Manager - Portfolio risk management and volatility targeting
Manages risk budget and ensures portfolio stays within target volatility
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RiskManager:
    """
    The Risk Manager handles:
    1. Risk Budget management (target volatility)
    2. Volatility targeting and adjustment
    3. Risk attribution analysis
    4. Portfolio risk monitoring
    """
    
    def __init__(self):
        # Asset class risk characteristics
        self.asset_risk_profiles = {
            'cash': {'volatility': 0.02, 'beta': 0.0, 'correlation': 0.0},
            'bonds': {'volatility': 0.05, 'beta': 0.3, 'correlation': 0.2},
            'shares': {'volatility': 0.20, 'beta': 1.0, 'correlation': 0.8},
            'commodities': {'volatility': 0.25, 'beta': 0.5, 'correlation': 0.3},
            'crypto': {'volatility': 0.60, 'beta': 2.0, 'correlation': 0.1}
        }
        
        # Risk limits
        self.risk_limits = {
            'max_volatility': 0.30,  # Maximum 30% volatility
            'min_volatility': 0.02,  # Minimum 2% volatility
            'max_single_asset': 0.40,  # Maximum 40% in single asset
            'max_asset_class': 0.70,  # Maximum 70% in single asset class
            'max_drawdown': 0.25     # Maximum 25% drawdown
        }
    
    def calculate_portfolio_volatility(self, allocation: Dict[str, float], 
                                     correlation_matrix: Optional[pd.DataFrame] = None) -> float:
        """
        Calculate portfolio volatility using asset class characteristics
        
        Args:
            allocation: Asset allocation dictionary
            correlation_matrix: Optional correlation matrix between assets
            
        Returns:
            Portfolio volatility (annualized)
        """
        # Get individual asset volatilities
        volatilities = []
        weights = []
        
        for asset_class, weight in allocation.items():
            if weight > 0 and asset_class in self.asset_risk_profiles:
                volatilities.append(self.asset_risk_profiles[asset_class]['volatility'])
                weights.append(weight)
        
        if not volatilities:
            return 0.0
        
        # Convert to numpy arrays
        vol_array = np.array(volatilities)
        weight_array = np.array(weights)
        
        # Normalize weights
        weight_array = weight_array / weight_array.sum()
        
        # Simple volatility calculation (assuming zero correlation for simplicity)
        # In production, you'd use the full correlation matrix
        portfolio_variance = np.sum((weight_array * vol_array) ** 2)
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        return float(portfolio_volatility)
    
    def calculate_risk_attribution(self, allocation: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate risk contribution by asset class
        
        Args:
            allocation: Asset allocation
            
        Returns:
            Risk attribution by asset class
        """
        risk_attribution = {}
        total_risk = 0.0
        
        for asset_class, weight in allocation.items():
            if weight > 0 and asset_class in self.asset_risk_profiles:
                asset_vol = self.asset_risk_profiles[asset_class]['volatility']
                risk_contribution = weight * asset_vol
                risk_attribution[asset_class] = risk_contribution
                total_risk += risk_contribution
        
        # Normalize to percentages
        if total_risk > 0:
            for asset_class in risk_attribution:
                risk_attribution[asset_class] = risk_attribution[asset_class] / total_risk
        
        return risk_attribution
    
    def adjust_for_risk_budget(self, allocation: Dict[str, float], 
                              target_volatility: float) -> Dict[str, float]:
        """
        Adjust allocation to meet target volatility
        
        Args:
            allocation: Current allocation
            target_volatility: Target portfolio volatility
            
        Returns:
            Risk-adjusted allocation
        """
        current_volatility = self.calculate_portfolio_volatility(allocation)
        
        if abs(current_volatility - target_volatility) < 0.01:  # Within 1%
            return allocation
        
        adjusted_allocation = allocation.copy()
        
        if current_volatility > target_volatility:
            # Reduce risk - move from risky to safe assets
            reduction_factor = target_volatility / current_volatility
            
            # Reduce risky assets
            risky_assets = ['shares', 'commodities', 'crypto']
            for asset in risky_assets:
                if asset in adjusted_allocation:
                    adjusted_allocation[asset] *= reduction_factor
            
            # Add to safe assets
            safe_assets = ['bonds', 'cash']
            total_reduction = sum(allocation.get(asset, 0) * (1 - reduction_factor) 
                               for asset in risky_assets if asset in allocation)
            
            # Distribute to safe assets
            for asset in safe_assets:
                if asset in adjusted_allocation:
                    adjusted_allocation[asset] += total_reduction / len(safe_assets)
        
        else:
            # Increase risk - move from safe to risky assets
            increase_factor = target_volatility / current_volatility
            
            # Increase risky assets
            risky_assets = ['shares', 'commodities']
            for asset in risky_assets:
                if asset in adjusted_allocation:
                    adjusted_allocation[asset] *= increase_factor
            
            # Reduce safe assets
            safe_assets = ['bonds', 'cash']
            total_increase = sum(allocation.get(asset, 0) * (increase_factor - 1) 
                               for asset in risky_assets if asset in allocation)
            
            # Distribute reduction across safe assets
            for asset in safe_assets:
                if asset in adjusted_allocation:
                    reduction = total_increase / len(safe_assets)
                    adjusted_allocation[asset] = max(0, adjusted_allocation[asset] - reduction)
        
        # Normalize allocation
        total = sum(adjusted_allocation.values())
        if total > 0:
            for key in adjusted_allocation:
                adjusted_allocation[key] /= total
        
        return adjusted_allocation
    
    def check_risk_limits(self, allocation: Dict[str, float]) -> Dict[str, bool]:
        """
        Check if allocation violates risk limits
        
        Args:
            allocation: Asset allocation
            
        Returns:
            Dictionary of limit violations
        """
        violations = {}
        
        # Check maximum single asset class
        max_class_weight = max(allocation.values()) if allocation else 0
        violations['max_asset_class'] = max_class_weight > self.risk_limits['max_asset_class']
        
        # Check portfolio volatility
        portfolio_vol = self.calculate_portfolio_volatility(allocation)
        violations['max_volatility'] = portfolio_vol > self.risk_limits['max_volatility']
        violations['min_volatility'] = portfolio_vol < self.risk_limits['min_volatility']
        
        # Check for negative allocations
        violations['negative_allocation'] = any(weight < 0 for weight in allocation.values())
        
        # Check allocation sum
        total_allocation = sum(allocation.values())
        violations['allocation_sum'] = abs(total_allocation - 1.0) > 0.01
        
        return violations
    
    def calculate_var_cvar(self, allocation: Dict[str, float], 
                          confidence_level: float = 0.95) -> Dict[str, float]:
        """
        Calculate Value at Risk (VaR) and Conditional VaR (CVaR)
        
        Args:
            allocation: Asset allocation
            confidence_level: Confidence level for VaR calculation
            
        Returns:
            VaR and CVaR metrics
        """
        # Simplified VaR calculation using normal distribution assumption
        portfolio_vol = self.calculate_portfolio_volatility(allocation)
        
        # Calculate VaR (assuming normal distribution)
        z_score = -1.645 if confidence_level == 0.95 else -2.326  # 95% or 99%
        var_1d = z_score * portfolio_vol / np.sqrt(252)  # Daily VaR
        var_1y = z_score * portfolio_vol  # Annual VaR
        
        # CVaR (Expected Shortfall) - simplified calculation
        cvar_1d = var_1d * 1.3  # Approximate CVaR
        cvar_1y = var_1y * 1.3
        
        return {
            'var_1d': var_1d,
            'var_1y': var_1y,
            'cvar_1d': cvar_1d,
            'cvar_1y': cvar_1y,
            'confidence_level': confidence_level,
            'portfolio_volatility': portfolio_vol
        }
    
    def generate_risk_report(self, allocation: Dict[str, float], 
                           target_volatility: float = 0.10) -> Dict:
        """
        Generate comprehensive risk report
        
        Args:
            allocation: Asset allocation
            target_volatility: Target volatility
            
        Returns:
            Complete risk report
        """
        # Calculate risk metrics
        portfolio_vol = self.calculate_portfolio_volatility(allocation)
        risk_attribution = self.calculate_risk_attribution(allocation)
        var_metrics = self.calculate_var_cvar(allocation)
        limit_violations = self.check_risk_limits(allocation)
        
        # Risk budget status
        vol_deviation = abs(portfolio_vol - target_volatility)
        vol_within_budget = vol_deviation < 0.02  # Within 2%
        
        return {
            'portfolio_volatility': portfolio_vol,
            'target_volatility': target_volatility,
            'volatility_deviation': vol_deviation,
            'within_risk_budget': vol_within_budget,
            'risk_attribution': risk_attribution,
            'var_metrics': var_metrics,
            'limit_violations': limit_violations,
            'risk_score': self._calculate_risk_score(allocation),
            'recommendations': self._generate_recommendations(allocation, target_volatility)
        }
    
    def _calculate_risk_score(self, allocation: Dict[str, float]) -> float:
        """Calculate overall risk score (0-1, higher = riskier)"""
        portfolio_vol = self.calculate_portfolio_volatility(allocation)
        max_vol = self.risk_limits['max_volatility']
        return min(1.0, portfolio_vol / max_vol)
    
    def _generate_recommendations(self, allocation: Dict[str, float], 
                                target_volatility: float) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []
        
        portfolio_vol = self.calculate_portfolio_volatility(allocation)
        
        if portfolio_vol > target_volatility * 1.1:  # 10% over target
            recommendations.append("Consider reducing allocation to high-risk assets (shares, commodities)")
        
        if portfolio_vol < target_volatility * 0.9:  # 10% under target
            recommendations.append("Consider increasing allocation to growth assets for better returns")
        
        # Check for concentration risk
        max_class = max(allocation.values()) if allocation else 0
        if max_class > 0.6:
            recommendations.append("Portfolio is concentrated in one asset class - consider diversification")
        
        # Check for too much cash
        if allocation.get('cash', 0) > 0.3:
            recommendations.append("High cash allocation may limit growth potential")
        
        return recommendations

# Example usage and testing
if __name__ == "__main__":
    # Initialize the Risk Manager
    risk_manager = RiskManager()
    
    # Test allocation
    test_allocation = {
        'shares': 0.55,
        'bonds': 0.25,
        'commodities': 0.10,
        'cash': 0.10
    }
    
    # Calculate portfolio volatility
    vol = risk_manager.calculate_portfolio_volatility(test_allocation)
    print(f"Portfolio volatility: {vol:.3f}")
    
    # Calculate risk attribution
    attribution = risk_manager.calculate_risk_attribution(test_allocation)
    print(f"Risk attribution: {attribution}")
    
    # Generate risk report
    report = risk_manager.generate_risk_report(test_allocation, target_volatility=0.10)
    print(f"\nRisk Report:")
    print(f"Volatility: {report['portfolio_volatility']:.3f}")
    print(f"Within budget: {report['within_risk_budget']}")
    print(f"Risk score: {report['risk_score']:.3f}")
    print(f"Recommendations: {report['recommendations']}")

