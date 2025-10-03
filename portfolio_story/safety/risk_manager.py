"""
The Risk Manager - Advanced Portfolio Risk Management and Analytics
Manages risk budget, volatility targeting, and provides comprehensive risk analytics
for the AI-powered portfolio management system.

This module implements sophisticated risk management techniques including:
- Value-at-Risk (VaR) and Conditional VaR (CVaR) calculations
- Monte Carlo simulation for risk assessment
- Stress testing and scenario analysis
- Risk attribution and factor analysis
- Dynamic risk budgeting and rebalancing
- Real-time risk monitoring and alerts
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
import logging
from datetime import datetime, timedelta
from scipy import stats
from scipy.optimize import minimize
import warnings

logger = logging.getLogger(__name__)

class RiskManager:
    """
    Advanced Risk Manager for AI-Powered Portfolio Management System
    
    This class provides comprehensive risk management capabilities for the portfolio
    management system, implementing sophisticated risk analytics and management
    techniques used in institutional portfolio management.
    
    Key Capabilities:
    1. Risk Budget Management: Target volatility tracking and adjustment
    2. Advanced Risk Metrics: VaR, CVaR, Expected Shortfall calculations
    3. Monte Carlo Simulation: Portfolio risk assessment using simulation methods
    4. Stress Testing: Scenario analysis and stress test implementation
    5. Risk Attribution: Factor-based risk decomposition and analysis
    6. Dynamic Rebalancing: Risk-based portfolio rebalancing strategies
    7. Real-time Monitoring: Continuous risk monitoring and alert systems
    
    The Risk Manager works in conjunction with the Markowitz optimization engine
    in the Planner class to provide comprehensive risk-aware portfolio management.
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
    
    def calculate_monte_carlo_var(self, allocation: Dict[str, float], 
                                returns_data: pd.DataFrame,
                                confidence_level: float = 0.95,
                                num_simulations: int = 10000,
                                time_horizon: int = 1) -> Dict[str, float]:
        """
        Calculate Value-at-Risk using Monte Carlo simulation.
        
        This method implements Monte Carlo simulation to estimate portfolio VaR,
        which is more robust than parametric VaR when return distributions
        deviate from normality.
        
        Args:
            allocation: Portfolio weights dictionary
            returns_data: Historical returns data (pandas DataFrame)
            confidence_level: VaR confidence level (default 95%)
            num_simulations: Number of Monte Carlo simulations
            time_horizon: Time horizon in days for VaR calculation
            
        Returns:
            Dictionary containing VaR metrics from Monte Carlo simulation
        """
        try:
            # Get portfolio returns
            portfolio_returns = self._calculate_portfolio_returns(allocation, returns_data)
            
            if len(portfolio_returns) < 30:  # Need sufficient data
                return self._fallback_var_calculation(allocation, confidence_level)
            
            # Fit distribution to returns (using t-distribution for fat tails)
            params = stats.t.fit(portfolio_returns)
            
            # Generate Monte Carlo scenarios
            mc_returns = stats.t.rvs(*params, size=num_simulations)
            
            # Calculate VaR from simulated returns
            var_percentile = (1 - confidence_level) * 100
            var_mc = np.percentile(mc_returns, var_percentile)
            
            # Calculate Expected Shortfall (CVaR)
            tail_returns = mc_returns[mc_returns <= var_mc]
            expected_shortfall = np.mean(tail_returns) if len(tail_returns) > 0 else var_mc
            
            # Scale to time horizon
            var_scaled = var_mc * np.sqrt(time_horizon)
            es_scaled = expected_shortfall * np.sqrt(time_horizon)
            
            return {
                'var_mc': var_scaled,
                'expected_shortfall': es_scaled,
                'confidence_level': confidence_level,
                'num_simulations': num_simulations,
                'time_horizon': time_horizon,
                'method': 'Monte Carlo'
            }
            
        except Exception as e:
            logger.warning(f"Monte Carlo VaR calculation failed: {e}")
            return self._fallback_var_calculation(allocation, confidence_level)
    
    def perform_stress_test(self, allocation: Dict[str, float],
                          stress_scenarios: Optional[Dict[str, Dict]] = None) -> Dict:
        """
        Perform stress testing on portfolio allocation.
        
        Stress testing evaluates portfolio performance under extreme but
        plausible market conditions, helping identify potential vulnerabilities.
        
        Args:
            allocation: Portfolio weights dictionary
            stress_scenarios: Custom stress scenarios (optional)
            
        Returns:
            Dictionary containing stress test results
        """
        if stress_scenarios is None:
            stress_scenarios = self._get_default_stress_scenarios()
        
        stress_results = {}
        
        for scenario_name, scenario_data in stress_scenarios.items():
            # Calculate portfolio return under stress scenario
            portfolio_stress_return = 0.0
            scenario_details = {}
            
            for asset_class, weight in allocation.items():
                if weight > 0 and asset_class in scenario_data:
                    asset_stress_return = scenario_data[asset_class]
                    portfolio_stress_return += weight * asset_stress_return
                    scenario_details[asset_class] = {
                        'weight': weight,
                        'stress_return': asset_stress_return,
                        'contribution': weight * asset_stress_return
                    }
            
            stress_results[scenario_name] = {
                'portfolio_return': portfolio_stress_return,
                'scenario_details': scenario_details,
                'severity': self._classify_stress_severity(portfolio_stress_return)
            }
        
        return stress_results
    
    def calculate_risk_contribution(self, weights: Dict[str, float],
                                  cov_matrix: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate risk contribution of each asset to portfolio risk.
        
        This method decomposes portfolio risk into individual asset contributions,
        which is essential for understanding risk concentration and for
        risk parity optimization approaches.
        
        Args:
            weights: Portfolio weights dictionary
            cov_matrix: Asset covariance matrix
            
        Returns:
            Dictionary of risk contributions by asset
        """
        try:
            # Convert weights to array aligned with covariance matrix
            weight_array = np.array([weights.get(asset, 0) for asset in cov_matrix.index])
            
            # Calculate portfolio variance
            portfolio_variance = np.dot(weight_array, np.dot(cov_matrix.values, weight_array))
            portfolio_volatility = np.sqrt(portfolio_variance)
            
            # Calculate marginal risk contributions
            marginal_contributions = np.dot(cov_matrix.values, weight_array) / portfolio_volatility
            
            # Calculate risk contributions
            risk_contributions = {}
            for i, asset in enumerate(cov_matrix.index):
                risk_contributions[asset] = weight_array[i] * marginal_contributions[i]
            
            # Normalize to percentages
            total_contribution = sum(risk_contributions.values())
            if total_contribution > 0:
                for asset in risk_contributions:
                    risk_contributions[asset] /= total_contribution
            
            return risk_contributions
            
        except Exception as e:
            logger.error(f"Risk contribution calculation failed: {e}")
            return {}
    
    def calculate_maximum_drawdown(self, returns_series: pd.Series) -> Dict[str, float]:
        """
        Calculate maximum drawdown and related metrics.
        
        Maximum drawdown is the largest peak-to-trough decline in portfolio value,
        which is a critical risk metric for understanding worst-case losses.
        
        Args:
            returns_series: Time series of portfolio returns
            
        Returns:
            Dictionary containing drawdown metrics
        """
        # Calculate cumulative returns
        cumulative_returns = (1 + returns_series).cumprod()
        
        # Calculate running maximum
        running_max = cumulative_returns.expanding().max()
        
        # Calculate drawdown
        drawdown = (cumulative_returns - running_max) / running_max
        
        # Find maximum drawdown
        max_drawdown = drawdown.min()
        max_dd_date = drawdown.idxmin()
        
        # Find peak before maximum drawdown
        peak_date = running_max.loc[:max_dd_date].idxmax()
        
        # Calculate recovery metrics
        recovery_time = None
        if max_dd_date < returns_series.index[-1]:
            recovery_series = cumulative_returns.loc[max_dd_date:]
            peak_value = running_max.loc[peak_date]
            recovery_mask = recovery_series >= peak_value
            if recovery_mask.any():
                recovery_date = recovery_series[recovery_mask].index[0]
                recovery_time = (recovery_date - max_dd_date).days
        
        return {
            'max_drawdown': max_drawdown,
            'max_dd_date': max_dd_date,
            'peak_date': peak_date,
            'recovery_time_days': recovery_time,
            'current_drawdown': drawdown.iloc[-1],
            'avg_drawdown': drawdown[drawdown < 0].mean() if (drawdown < 0).any() else 0
        }
    
    def calculate_tail_risk_metrics(self, returns_series: pd.Series) -> Dict[str, float]:
        """
        Calculate tail risk metrics including skewness and kurtosis.
        
        Tail risk metrics help identify the potential for extreme losses
        beyond what normal distribution assumptions would predict.
        
        Args:
            returns_series: Time series of portfolio returns
            
        Returns:
            Dictionary containing tail risk metrics
        """
        returns_clean = returns_series.dropna()
        
        if len(returns_clean) < 30:
            return {'error': 'Insufficient data for tail risk calculation'}
        
        # Calculate moments
        mean_return = returns_clean.mean()
        volatility = returns_clean.std()
        skewness = stats.skew(returns_clean)
        kurtosis = stats.kurtosis(returns_clean)
        
        # Calculate tail ratios
        var_95 = np.percentile(returns_clean, 5)
        var_99 = np.percentile(returns_clean, 1)
        
        # Expected shortfall
        tail_95 = returns_clean[returns_clean <= var_95]
        es_95 = tail_95.mean() if len(tail_95) > 0 else var_95
        
        tail_99 = returns_clean[returns_clean <= var_99]
        es_99 = tail_99.mean() if len(tail_99) > 0 else var_99
        
        return {
            'skewness': skewness,
            'kurtosis': kurtosis,
            'var_95': var_95,
            'var_99': var_99,
            'expected_shortfall_95': es_95,
            'expected_shortfall_99': es_99,
            'tail_ratio_95': abs(es_95 / var_95) if var_95 != 0 else 0,
            'tail_ratio_99': abs(es_99 / var_99) if var_99 != 0 else 0,
            'excess_kurtosis': kurtosis - 3,  # Excess kurtosis (normal = 0)
            'tail_risk_score': self._calculate_tail_risk_score(skewness, kurtosis)
        }
    
    def _calculate_portfolio_returns(self, allocation: Dict[str, float], 
                                   returns_data: pd.DataFrame) -> pd.Series:
        """Helper method to calculate portfolio returns from allocation and asset returns."""
        portfolio_returns = pd.Series(0, index=returns_data.index)
        
        for asset_class, weight in allocation.items():
            if weight > 0 and asset_class in returns_data.columns:
                portfolio_returns += weight * returns_data[asset_class]
        
        return portfolio_returns
    
    def _fallback_var_calculation(self, allocation: Dict[str, float], 
                                confidence_level: float) -> Dict[str, float]:
        """Fallback VaR calculation when Monte Carlo fails."""
        portfolio_vol = self.calculate_portfolio_volatility(allocation)
        z_score = -1.645 if confidence_level == 0.95 else -2.326
        var_value = z_score * portfolio_vol
        
        return {
            'var_mc': var_value,
            'expected_shortfall': var_value * 1.3,
            'confidence_level': confidence_level,
            'method': 'Parametric Fallback'
        }
    
    def _get_default_stress_scenarios(self) -> Dict[str, Dict]:
        """Get default stress test scenarios."""
        return {
            'Financial Crisis 2008': {
                'shares': -0.50,  # 50% decline in equities
                'bonds': 0.10,    # Flight to quality
                'commodities': -0.30,
                'crypto': -0.80,
                'cash': 0.02
            },
            'COVID-19 Crash 2020': {
                'shares': -0.35,
                'bonds': 0.05,
                'commodities': -0.25,
                'crypto': -0.50,
                'cash': 0.01
            },
            'Inflation Shock': {
                'shares': -0.20,
                'bonds': -0.15,
                'commodities': 0.40,
                'crypto': -0.30,
                'cash': -0.05
            },
            'Interest Rate Shock': {
                'shares': -0.15,
                'bonds': -0.25,
                'commodities': -0.10,
                'crypto': -0.20,
                'cash': 0.05
            }
        }
    
    def _classify_stress_severity(self, portfolio_return: float) -> str:
        """Classify stress test severity based on portfolio return."""
        if portfolio_return < -0.30:
            return 'Extreme'
        elif portfolio_return < -0.20:
            return 'Severe'
        elif portfolio_return < -0.10:
            return 'Moderate'
        else:
            return 'Mild'
    
    def _calculate_tail_risk_score(self, skewness: float, kurtosis: float) -> float:
        """Calculate a composite tail risk score."""
        # Normalize skewness and kurtosis to 0-1 scale
        skew_score = abs(skewness) / 2.0  # Cap at 2 for extreme skewness
        kurt_score = max(0, kurtosis - 3) / 5.0  # Excess kurtosis, cap at 5
        
        # Combine scores (equal weighting)
        tail_risk_score = (skew_score + kurt_score) / 2.0
        return min(1.0, tail_risk_score)  # Cap at 1.0

# Example usage and testing
if __name__ == "__main__":
    # Initialize the Advanced Risk Manager
    risk_manager = RiskManager()
    
    # Test portfolio allocation
    test_allocation = {
        'shares': 0.55,
        'bonds': 0.25,
        'commodities': 0.10,
        'cash': 0.10
    }
    
    print("=== AI Portfolio Risk Manager - Advanced Risk Analytics Demo ===\n")
    
    # 1. Basic Risk Metrics
    print("1. BASIC RISK METRICS")
    print("-" * 40)
    vol = risk_manager.calculate_portfolio_volatility(test_allocation)
    print(f"Portfolio volatility: {vol:.3f} ({vol*100:.1f}%)")
    
    attribution = risk_manager.calculate_risk_attribution(test_allocation)
    print(f"Risk attribution: {attribution}")
    
    # 2. VaR and Risk Metrics
    print("\n2. VALUE-AT-RISK (VaR) ANALYSIS")
    print("-" * 40)
    var_metrics = risk_manager.calculate_var_cvar(test_allocation)
    print(f"VaR (95% confidence): {var_metrics['var_1d']:.3f} daily, {var_metrics['var_1y']:.3f} annual")
    print(f"CVaR (Expected Shortfall): {var_metrics['cvar_1d']:.3f} daily, {var_metrics['cvar_1y']:.3f} annual")
    
    # 3. Stress Testing
    print("\n3. STRESS TESTING")
    print("-" * 40)
    stress_results = risk_manager.perform_stress_test(test_allocation)
    for scenario, results in stress_results.items():
        print(f"{scenario}: {results['portfolio_return']:.1%} ({results['severity']} severity)")
    
    # 4. Risk Limits Check
    print("\n4. RISK LIMITS COMPLIANCE")
    print("-" * 40)
    violations = risk_manager.check_risk_limits(test_allocation)
    for limit, violated in violations.items():
        status = "VIOLATED" if violated else "OK"
        print(f"{limit.replace('_', ' ').title()}: {status}")
    
    # 5. Comprehensive Risk Report
    print("\n5. COMPREHENSIVE RISK REPORT")
    print("-" * 40)
    report = risk_manager.generate_risk_report(test_allocation, target_volatility=0.10)
    print(f"Portfolio volatility: {report['portfolio_volatility']:.3f}")
    print(f"Target volatility: {report['target_volatility']:.3f}")
    print(f"Volatility deviation: {report['volatility_deviation']:.3f}")
    print(f"Within risk budget: {report['within_risk_budget']}")
    print(f"Overall risk score: {report['risk_score']:.3f}")
    print(f"Recommendations: {report['recommendations']}")
    
    # 6. Advanced Risk Metrics (if we had returns data)
    print("\n6. ADVANCED RISK ANALYTICS")
    print("-" * 40)
    print("Note: Advanced metrics like Monte Carlo VaR, maximum drawdown,")
    print("and tail risk metrics require historical returns data.")
    print("These would be calculated in the full portfolio management workflow.")
    
    print("\n=== Demo Complete ===")
    print("The Risk Manager is now ready for integration with the Markowitz")
    print("optimization engine in the Planner class for comprehensive")
    print("risk-aware portfolio management.")

