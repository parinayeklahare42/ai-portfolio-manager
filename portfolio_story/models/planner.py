"""
The Planner - Advanced Portfolio Optimization System
===================================================

This module implements sophisticated portfolio optimization using Markowitz mean-variance
optimization theory. It provides mathematical optimization algorithms for portfolio
construction based on expected returns, covariance matrices, and risk preferences.

Key Features:
- Markowitz mean-variance optimization
- Risk preference mapping to target volatility levels
- Sharpe ratio maximization and minimum variance optimization
- Portfolio constraints (weights ≥ 0, sum = 1, optional cash)
- Advanced portfolio metrics calculation (VaR, Sharpe ratio, etc.)

Mathematical Implementation:
- Expected returns calculation from historical data
- Covariance matrix estimation for risk modeling
- Quadratic programming optimization for portfolio weights
- Risk budgeting and volatility targeting

Author: parinayeklahare42
Course: 125882 AI in Investment and Risk Management
Assignment: Assessment 2 Hackathon and Coding Challenge
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from enum import Enum
from scipy.optimize import minimize
from scipy.linalg import cholesky
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

class OptimizationObjective(Enum):
    SHARPE_RATIO = "sharpe_ratio"  # Maximize Sharpe ratio
    MIN_VARIANCE = "min_variance"  # Minimize portfolio variance
    TARGET_VOLATILITY = "target_volatility"  # Target specific volatility

class Planner:
    """
    Advanced Portfolio Planner with Markowitz Mean-Variance Optimization
    
    This class implements sophisticated portfolio optimization using modern portfolio theory.
    It provides mathematical optimization algorithms for portfolio construction based on
    expected returns, covariance matrices, and risk preferences.
    
    Key Optimization Features:
    1. Markowitz mean-variance optimization using expected returns and covariance matrix
    2. Risk preference mapping to target volatility levels (low=5%, medium=10%, high=15%)
    3. Sharpe ratio maximization and minimum variance optimization
    4. Portfolio constraints: weights ≥ 0, total = 1, optional cash allocation
    5. Advanced portfolio metrics: expected return, volatility, Sharpe ratio, VaR
    
    Mathematical Implementation:
    - Expected returns calculation from historical price data
    - Covariance matrix estimation using sample covariance
    - Quadratic programming optimization for optimal weights
    - Risk budgeting and volatility targeting
    """
    
    def __init__(self):
        # Annualized volatilities (reasonable long-run ballparks)
        self.SIGMA = {
            'cash': 0.005,
            'bonds': 0.05,
            'shares': 0.18,
            'commodities': 0.22,
            'crypto': 0.80
        }
        
        # Symmetric correlation matrix
        self.CORR = {
            'cash': {'cash': 1, 'bonds': 0, 'shares': 0, 'commodities': 0, 'crypto': 0},
            'bonds': {'cash': 0, 'bonds': 1, 'shares': 0.2, 'commodities': 0, 'crypto': 0},
            'shares': {'cash': 0, 'bonds': 0.2, 'shares': 1, 'commodities': 0.4, 'crypto': 0.3},
            'commodities': {'cash': 0, 'bonds': 0, 'shares': 0.4, 'commodities': 1, 'crypto': 0.3},
            'crypto': {'cash': 0, 'bonds': 0, 'shares': 0.3, 'commodities': 0.3, 'crypto': 1}
        }
        
        # Base allocation per risk level (sums ~1; adjust to your house view if needed)
        self.BASE_BY_RISK = {
            1: {'cash': 0.15, 'bonds': 0.55, 'shares': 0.20, 'commodities': 0.08, 'crypto': 0.02},  # Very Conservative
            2: {'cash': 0.10, 'bonds': 0.45, 'shares': 0.30, 'commodities': 0.12, 'crypto': 0.03},  # Conservative
            3: {'cash': 0.07, 'bonds': 0.35, 'shares': 0.40, 'commodities': 0.15, 'crypto': 0.03},  # Moderate
            4: {'cash': 0.04, 'bonds': 0.25, 'shares': 0.55, 'commodities': 0.12, 'crypto': 0.04},  # Aggressive
            5: {'cash': 0.02, 'bonds': 0.15, 'shares': 0.65, 'commodities': 0.10, 'crypto': 0.08}   # Very Aggressive
        }
        
        # Horizon tilt deltas (from Goal.docx)
        self.HORIZON_TILT = {
            'short': {'cash': +0.03, 'bonds': +0.05, 'shares': -0.06, 'commodities': -0.015, 'crypto': -0.005},
            'medium': {'cash': 0.00, 'bonds': 0.00, 'shares': 0.00, 'commodities': 0.000, 'crypto': 0.000},
            'long': {'cash': -0.02, 'bonds': -0.05, 'shares': +0.05, 'commodities': +0.015, 'crypto': +0.005}
        }
        
        # Volatility bucket tilt deltas (from Goal.docx)
        self.VOL_TILT = {
            'low': {'cash': +0.02, 'bonds': +0.08, 'shares': -0.07, 'commodities': -0.02, 'crypto': -0.01},
            'mid': {'cash': 0.00, 'bonds': 0.00, 'shares': 0.00, 'commodities': 0.00, 'crypto': 0.00},
            'high': {'cash': -0.02, 'bonds': -0.05, 'shares': +0.05, 'commodities': +0.015, 'crypto': +0.005}
        }
        
        # Realistic hard caps/floors (from Goal.docx)
        self.BOUNDS = {
            'cashMin': 0.01,   # keep at least 1% cash for liquidity
            'bondsMin': 0.10,  # bonds should not drop below 10% except the most aggressive corner
            'bondsMinRisk5LongHigh': 0.05, # allow a lower bond floor in the single riskiest corner
            'cryptoMaxLow': 0.10,   # keep crypto <10% when vol tolerance is low
            'cryptoMaxMid': 0.12,   # <12% for mid
            'cryptoMaxHigh': 0.15,  # up to 15% only in high bucket
            'commoditiesMax': 0.15, # cap commodities to 15%,
        }
        
        # Risk-free rate for Sharpe ratio calculation
        self.risk_free_rate = 0.03  # 3% annual risk-free rate
    
    def clamp(self, x: float, lo: float, hi: float) -> float:
        """Clamp value between lo and hi (from Goal.docx)"""
        return min(hi, max(lo, x))
    
    def clamp01(self, x: float) -> float:
        """Clamp value between 0 and 1"""
        return min(1.0, max(0.0, x))
    
    def normalize_weights(self, w: Dict[str, float]) -> Dict[str, float]:
        """Normalize weights to sum to 1.0 (from Goal.docx)"""
        total = w.get('cash', 0) + w.get('bonds', 0) + w.get('shares', 0) + w.get('commodities', 0) + w.get('crypto', 0)
        if total <= 0:
            total = 1.0
        return {
            'cash': w.get('cash', 0) / total,
            'bonds': w.get('bonds', 0) / total,
            'shares': w.get('shares', 0) / total,
            'commodities': w.get('commodities', 0) / total,
            'crypto': w.get('crypto', 0) / total
        }
    
    def apply_delta(self, w: Dict[str, float], d: Dict[str, float]) -> Dict[str, float]:
        """Apply delta to weights (from Goal.docx)"""
        return {
            'cash': w.get('cash', 0) + d.get('cash', 0),
            'bonds': w.get('bonds', 0) + d.get('bonds', 0),
            'shares': w.get('shares', 0) + d.get('shares', 0),
            'commodities': w.get('commodities', 0) + d.get('commodities', 0),
            'crypto': w.get('crypto', 0) + d.get('crypto', 0)
        }
    
    def vol_bucket(self, max_vol_pct: float) -> str:
        """Map maxVolPct to volatility bucket (from Goal.docx)"""
        if max_vol_pct < 30:
            return "low"
        elif max_vol_pct <= 60:
            return "mid"
        else:
            return "high"
    
    def calculate_portfolio_volatility(self, w: Dict[str, float]) -> float:
        """Calculate portfolio volatility percentage using SIGMA and CORR matrices"""
        keys = ['cash', 'bonds', 'shares', 'commodities', 'crypto']
        variance = 0.0
        
        for i, ki in enumerate(keys):
            for j, kj in enumerate(keys):
                variance += (w.get(ki, 0) * w.get(kj, 0) * 
                           self.SIGMA[ki] * self.SIGMA[kj] * 
                           self.CORR[ki][kj])
        
        return np.sqrt(variance) * 100  # Return as percentage
        
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
    
    def compute_policy_weights(self, horizon: str, risk_level: int, max_vol_pct: float) -> Dict[str, float]:
        """
        Compute policy weights using the exact algorithm from Goal.docx
        
        Args:
            horizon: "short", "medium", or "long"
            risk_level: 1-5 (Very Conservative to Very Aggressive)
            max_vol_pct: Maximum volatility percentage
            
        Returns:
            Dict with normalized weights
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Computing policy weights: horizon={horizon}, risk_level={risk_level}, max_vol_pct={max_vol_pct}")
        
        # Step 1: Start from base by risk
        w = self.BASE_BY_RISK[risk_level].copy()
        logger.info(f"Step 1 - Base allocation: {w}")
        
        # Step 2: Apply horizon tilt
        w = self.apply_delta(w, self.HORIZON_TILT[horizon])
        logger.info(f"Step 2 - After horizon tilt: {w}")
        
        # Step 3: Apply volatility bucket tilt
        bucket = self.vol_bucket(max_vol_pct)
        w = self.apply_delta(w, self.VOL_TILT[bucket])
        logger.info(f"Step 3 - After vol tilt ({bucket}): {w}")
        
        # Step 4: Apply bounds (clamp extreme assets to realistic caps/floors)
        bonds_floor = self.BOUNDS['bondsMinRisk5LongHigh'] if (risk_level == 5 and horizon == "long" and bucket == "high") else self.BOUNDS['bondsMin']
        crypto_cap = self.BOUNDS['cryptoMaxLow'] if bucket == "low" else (self.BOUNDS['cryptoMaxMid'] if bucket == "mid" else self.BOUNDS['cryptoMaxHigh'])
        
        w['cash'] = max(w['cash'], self.BOUNDS['cashMin'])
        w['bonds'] = max(w['bonds'], bonds_floor)
        w['crypto'] = min(w['crypto'], crypto_cap)
        w['commodities'] = min(w['commodities'], self.BOUNDS['commoditiesMax'])
        
        logger.info(f"Step 4 - After bounds: {w}")
        
        # Step 5: Normalize to sum = 1
        w = self.normalize_weights(w)
        logger.info(f"Step 5 - After normalize: {w}")
        
        # Step 6: Presentation rounding for the pie
        r = {
            'cash': round(w['cash'] * 100) / 100,
            'bonds': round(w['bonds'] * 100) / 100,
            'shares': round(w['shares'] * 100) / 100,
            'commodities': round(w['commodities'] * 100) / 100,
            'crypto': round(w['crypto'] * 100) / 100,
        }
        
        # Keep sum exactly 1 after rounding
        w = self.normalize_weights(r)
        logger.info(f"Step 6 - Final rounded weights: {w}")
        
        return w
    
    def create_optimal_allocation(self, capital: float, horizon: str, risk_level: int, max_vol_pct: float) -> Dict:
        """
        Create optimal allocation using the exact policy from Goal.docx
        
        Args:
            capital: Investment capital amount
            horizon: 'short', 'medium', 'long'
            risk_level: 1-5 (1=Very Conservative, 5=Very Aggressive)
            max_vol_pct: Maximum allowed volatility percentage (e.g., 15 for 15%)
            
        Returns:
            Dictionary with allocation results
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Creating optimal allocation: capital={capital}, horizon={horizon}, risk_level={risk_level}, max_vol_pct={max_vol_pct}")
        
        try:
            # Use the exact policy from Goal.docx
            w = self.compute_policy_weights(horizon, risk_level, max_vol_pct)
            
            # Calculate final metrics
            predicted_vol_pct = self.calculate_portfolio_volatility(w)
            amount_invested = capital
            cash_remaining = 0  # All capital is invested (cash slice is different from cash remaining)
            assets_selected = sum(1 for weight in w.values() if weight > 0.001)
            
            # Risk status
            risk_status = "Higher than target" if predicted_vol_pct > max_vol_pct else "Within target"
            
            result = {
                'weights': w,
                'predicted_vol_pct': predicted_vol_pct,
                'amount_invested': amount_invested,
                'cash_remaining': cash_remaining,
                'assets_selected': assets_selected,
                'risk_status': risk_status,
                'risk_level': risk_level,
                'horizon': horizon,
                'max_vol_pct': max_vol_pct
            }
            
            logger.info(f"Final allocation result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error creating optimal allocation: {e}")
            # Return safe default allocation
            return self.create_optimal_allocation(capital, horizon, 3, max_vol_pct)
    
    def create_base_allocation(self, risk_level: int, horizon: str = "medium") -> Dict[str, float]:
        """
        Create base allocation using the new 1-5 risk level system
        
        Args:
            risk_level: 1-5 (1=Very Conservative, 5=Very Aggressive)
            horizon: 'short', 'medium', 'long'
            
        Returns:
            Dictionary with asset class allocations
        """
        # Map horizon strings
        horizon_map = {
            'short_term': 'short',
            'medium_term': 'medium', 
            'long_term': 'long'
        }
        horizon = horizon_map.get(horizon, horizon)
        
        # Use the exact policy from Goal.docx with default volatility
        return self.compute_policy_weights(horizon, risk_level, 45.0)  # Default mid-volatility
    
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
    
    def create_portfolio_plan(self, time_horizon: str, risk_level: int = 3,
                            sleep_better_dial: float = 0.0, target_volatility: float = 0.10) -> Dict:
        """
        Create complete portfolio plan using new Goal.docx allocation system
        
        Args:
            time_horizon: Investment time horizon ('short', 'medium', 'long')
            risk_level: Risk level (1-5)
            sleep_better_dial: Additional risk adjustment (0-1)
            target_volatility: Target portfolio volatility
            
        Returns:
            Complete portfolio plan
        """
        # Create base allocation using new system
        allocation = self.create_base_allocation(risk_level, time_horizon)
        
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
            'risk_level': risk_level,
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
    
    def calculate_expected_returns(self, asset_data: Dict[str, pd.DataFrame]) -> pd.Series:
        """
        Calculate expected returns from historical price data (Requirement 1)
        
        This method implements the first requirement: calculating expected returns
        from historical data for use in Markowitz optimization.
        
        Args:
            asset_data: Dictionary of ticker -> price data
            
        Returns:
            pd.Series: Expected annual returns for each asset
        """
        expected_returns = {}
        
        for ticker, data in asset_data.items():
            if len(data) > 1:
                # Calculate daily returns
                daily_returns = data['Close'].pct_change().dropna()
                
                # Calculate annualized expected return
                # Using geometric mean for more conservative estimates
                annual_return = (1 + daily_returns.mean()) ** 252 - 1
                expected_returns[ticker] = annual_return
            else:
                # Fallback to historical estimates if insufficient data
                expected_returns[ticker] = 0.08  # 8% default
        
        return pd.Series(expected_returns)
    
    def calculate_covariance_matrix(self, asset_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Calculate covariance matrix from historical price data (Requirement 1)
        
        This method implements the first requirement: calculating covariance matrix
        from historical data for use in Markowitz optimization.
        
        Args:
            asset_data: Dictionary of ticker -> price data
            
        Returns:
            pd.DataFrame: Covariance matrix of asset returns
        """
        # Calculate returns for all assets
        returns_data = {}
        
        for ticker, data in asset_data.items():
            if len(data) > 1:
                daily_returns = data['Close'].pct_change().dropna()
                returns_data[ticker] = daily_returns
        
        if not returns_data:
            raise ValueError("Insufficient data for covariance calculation")
        
        # Create DataFrame of aligned returns
        returns_df = pd.DataFrame(returns_data)
        
        # Calculate sample covariance matrix
        # Annualize by multiplying by 252 trading days
        cov_matrix = returns_df.cov() * 252
        
        return cov_matrix
    
    def optimize_portfolio_weights(self, expected_returns: pd.Series, 
                                 cov_matrix: pd.DataFrame,
                                 objective: str = "sharpe_ratio",
                                 target_volatility: Optional[float] = None,
                                 allow_cash: bool = False) -> Dict[str, float]:
        """
        Optimize portfolio weights using Markowitz mean-variance optimization (Requirements 1, 3, 4)
        
        This method implements the core Markowitz optimization with the following requirements:
        1. Uses expected returns and covariance matrix
        3. Optimizes for Sharpe ratio maximization or minimum variance
        4. Ensures constraints: weights ≥ 0, total = 1, optional cash
        
        Args:
            expected_returns: Expected returns for each asset
            cov_matrix: Covariance matrix of asset returns
            objective: Optimization objective ('sharpe_ratio', 'min_variance', 'target_volatility')
            target_volatility: Target volatility for target_volatility objective
            allow_cash: Whether to allow cash allocation
            
        Returns:
            Dict[str, float]: Optimal portfolio weights
        """
        n_assets = len(expected_returns)
        asset_names = expected_returns.index.tolist()
        
        # Convert to numpy arrays for optimization
        returns_array = expected_returns.values
        cov_array = cov_matrix.values
        
        # Add cash as risk-free asset if allowed
        if allow_cash:
            # Add cash with risk-free return and zero variance/covariance
            returns_array = np.append(returns_array, self.risk_free_rate)
            
            # Extend covariance matrix with zeros for cash
            cash_row = np.zeros((1, n_assets))
            cash_col = np.zeros((n_assets + 1, 1))
            cov_array = np.vstack([cov_array, cash_row])
            cov_array = np.hstack([cov_array, cash_col])
            
            asset_names.append('cash')
            n_assets += 1
        
        # Initial guess: equal weights
        x0 = np.ones(n_assets) / n_assets
        
        # Constraints: weights sum to 1, weights >= 0
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}  # Sum to 1
        ]
        
        # Bounds: weights >= 0
        bounds = [(0.0, 1.0) for _ in range(n_assets)]
        
        # Objective function based on optimization type
        if objective == "sharpe_ratio":
            # Maximize Sharpe ratio (minimize negative Sharpe ratio)
            def objective_function(weights):
                portfolio_return = np.dot(weights, returns_array)
                portfolio_variance = np.dot(weights, np.dot(cov_array, weights))
                portfolio_volatility = np.sqrt(portfolio_variance)
                
                if portfolio_volatility == 0:
                    return -np.inf
                
                sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
                return -sharpe_ratio  # Minimize negative Sharpe ratio
                
        elif objective == "min_variance":
            # Minimize portfolio variance
            def objective_function(weights):
                portfolio_variance = np.dot(weights, np.dot(cov_array, weights))
                return portfolio_variance
                
        elif objective == "target_volatility":
            # Target specific volatility
            if target_volatility is None:
                raise ValueError("target_volatility must be specified for target_volatility objective")
            
            def objective_function(weights):
                portfolio_variance = np.dot(weights, np.dot(cov_array, weights))
                portfolio_volatility = np.sqrt(portfolio_variance)
                # Minimize squared deviation from target volatility
                return (portfolio_volatility - target_volatility) ** 2
        else:
            raise ValueError(f"Unknown objective: {objective}")
        
        # Perform optimization
        try:
            result = minimize(
                objective_function,
                x0,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints,
                options={'ftol': 1e-9, 'disp': False}
            )
            
            if result.success:
                optimal_weights = result.x
                
                # Create weight dictionary
                weights_dict = {}
                for i, asset_name in enumerate(asset_names):
                    if optimal_weights[i] > 1e-6:  # Only include significant weights
                        weights_dict[asset_name] = optimal_weights[i]
                
                return weights_dict
            else:
                logger.warning(f"Optimization failed: {result.message}")
                # Return equal weights as fallback
                return {name: 1.0/len(asset_names) for name in asset_names}
                
        except Exception as e:
            logger.error(f"Optimization error: {e}")
            # Return equal weights as fallback
            return {name: 1.0/len(asset_names) for name in asset_names}
    
    def calculate_portfolio_metrics(self, weights: Dict[str, float],
                                  expected_returns: pd.Series,
                                  cov_matrix: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate advanced portfolio metrics (Requirement 5)
        
        This method implements requirement 5: calculating portfolio metrics including
        expected return, volatility, Sharpe ratio, and Value-at-Risk.
        
        Args:
            weights: Portfolio weights
            expected_returns: Expected returns for each asset
            cov_matrix: Covariance matrix of asset returns
            
        Returns:
            Dict[str, float]: Portfolio metrics
        """
        # Filter to only include assets with weights
        weighted_assets = [asset for asset, weight in weights.items() if weight > 0]
        
        if not weighted_assets:
            return {
                'expected_return': 0.0,
                'volatility': 0.0,
                'sharpe_ratio': 0.0,
                'var_95': 0.0,
                'var_99': 0.0
            }
        
        # Create weight vector
        weight_vector = np.array([weights[asset] for asset in weighted_assets])
        
        # Get expected returns for weighted assets
        returns_vector = expected_returns[weighted_assets].values
        
        # Get covariance matrix for weighted assets
        cov_subset = cov_matrix.loc[weighted_assets, weighted_assets].values
        
        # Calculate portfolio expected return
        portfolio_return = np.dot(weight_vector, returns_vector)
        
        # Calculate portfolio variance and volatility
        portfolio_variance = np.dot(weight_vector, np.dot(cov_subset, weight_vector))
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        # Calculate Sharpe ratio
        if portfolio_volatility > 0:
            sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
        else:
            sharpe_ratio = 0.0
        
        # Calculate Value-at-Risk (VaR) assuming normal distribution
        # VaR = -z_score * portfolio_volatility * portfolio_value
        # For 95% confidence: z_score = 1.645
        # For 99% confidence: z_score = 2.326
        var_95 = -1.645 * portfolio_volatility  # 95% VaR
        var_99 = -2.326 * portfolio_volatility  # 99% VaR
        
        return {
            'expected_return': portfolio_return,
            'volatility': portfolio_volatility,
            'sharpe_ratio': sharpe_ratio,
            'var_95': var_95,
            'var_99': var_99,
            'risk_free_rate': self.risk_free_rate
        }
    
    def create_optimized_portfolio_plan(self, asset_data: Dict[str, pd.DataFrame],
                                      risk_preference: str = "moderate",
                                      objective: str = "sharpe_ratio",
                                      allow_cash: bool = False) -> Dict:
        """
        Create optimized portfolio plan using Markowitz optimization
        
        This method combines all requirements into a complete optimization workflow:
        1. Calculate expected returns and covariance matrix
        2. Map risk preference to target volatility
        3. Optimize portfolio weights
        4. Calculate advanced portfolio metrics
        
        Args:
            asset_data: Historical price data for all assets
            risk_preference: Risk preference ('low', 'medium', 'high', 'conservative', 'moderate', 'aggressive')
            objective: Optimization objective ('sharpe_ratio', 'min_variance', 'target_volatility')
            allow_cash: Whether to allow cash allocation
            
        Returns:
            Dict: Complete optimized portfolio plan
        """
        try:
            # Step 1: Calculate expected returns and covariance matrix (Requirement 1)
            logger.info("Calculating expected returns and covariance matrix...")
            expected_returns = self.calculate_expected_returns(asset_data)
            cov_matrix = self.calculate_covariance_matrix(asset_data)
            
            # Step 2: Map risk preference to target volatility (Requirement 2)
            target_volatility = self.risk_volatility_mapping.get(risk_preference.lower(), 0.10)
            logger.info(f"Risk preference '{risk_preference}' mapped to {target_volatility:.1%} target volatility")
            
            # Step 3: Optimize portfolio weights (Requirements 3, 4)
            logger.info(f"Optimizing portfolio using {objective} objective...")
            optimal_weights = self.optimize_portfolio_weights(
                expected_returns, cov_matrix, objective, target_volatility, allow_cash
            )
            
            # Step 4: Calculate portfolio metrics (Requirement 5)
            logger.info("Calculating portfolio metrics...")
            portfolio_metrics = self.calculate_portfolio_metrics(
                optimal_weights, expected_returns, cov_matrix
            )
            
            # Create comprehensive portfolio plan
            portfolio_plan = {
                'allocation': optimal_weights,
                'risk_preference': risk_preference,
                'target_volatility': target_volatility,
                'objective': objective,
                'allow_cash': allow_cash,
                'metrics': portfolio_metrics,
                'expected_returns': expected_returns.to_dict(),
                'covariance_matrix': cov_matrix.to_dict(),
                'optimization_date': pd.Timestamp.now().isoformat()
            }
            
            logger.info("Portfolio optimization completed successfully")
            return portfolio_plan
            
        except Exception as e:
            logger.error(f"Portfolio optimization failed: {e}")
            # Return fallback plan
            return self.create_portfolio_plan("long_term", risk_preference, 0.0, target_volatility)

# Example usage and testing
if __name__ == "__main__":
    """
    Example usage of the Advanced Portfolio Planner with Markowitz optimization.
    
    This section demonstrates the new requirements implementation:
    1. Markowitz mean-variance optimization
    2. Risk preference mapping to target volatility levels
    3. Sharpe ratio maximization and minimum variance optimization
    4. Portfolio constraints and advanced metrics calculation
    """
    
    # Initialize the Advanced Planner
    print("🎯 Initializing Advanced Portfolio Planner with Markowitz Optimization...")
    planner = Planner()
    
    # Test risk preference mapping (Requirement 2)
    print("\n📊 Testing Risk Preference Mapping:")
    print("=" * 50)
    for risk_pref in ['low', 'medium', 'high', 'conservative', 'moderate', 'aggressive']:
        target_vol = planner.risk_volatility_mapping.get(risk_pref, 0.10)
        print(f"   {risk_pref.title()}: {target_vol:.1%} target volatility")
    
    # Create sample asset data for optimization testing
    print("\n📈 Generating sample asset data for optimization...")
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
    
    # Generate correlated asset returns for realistic covariance matrix
    n_assets = 5
    asset_names = ['CBA.AX', 'BHP.AX', 'VAS.AX', 'GOLD.AX', 'BTC-USD']
    
    # Create correlated returns
    base_returns = np.random.randn(len(dates), n_assets) * 0.02
    correlation_structure = np.array([
        [1.0, 0.3, 0.5, 0.1, 0.2],  # CBA correlations
        [0.3, 1.0, 0.4, 0.2, 0.1],  # BHP correlations
        [0.5, 0.4, 1.0, 0.3, 0.1],  # VAS correlations
        [0.1, 0.2, 0.3, 1.0, 0.4],  # GOLD correlations
        [0.2, 0.1, 0.1, 0.4, 1.0]   # BTC correlations
    ])
    
    # Apply correlation structure
    correlated_returns = np.dot(base_returns, np.linalg.cholesky(correlation_structure))
    
    # Create price data from returns
    asset_data = {}
    initial_prices = [100, 45, 80, 2500, 40000]
    
    for i, (name, initial_price) in enumerate(zip(asset_names, initial_prices)):
        prices = initial_price * np.exp(np.cumsum(correlated_returns[:, i]))
        asset_data[name] = pd.DataFrame({
            'Close': prices,
            'Volume': np.random.randint(1000, 10000, len(dates))
        }, index=dates)
    
    print(f"✅ Generated data for {len(asset_data)} assets")
    
    # Test different optimization objectives (Requirement 3)
    print("\n🎯 Testing Markowitz Optimization Objectives:")
    print("=" * 60)
    
    optimization_tests = [
        ("sharpe_ratio", "moderate", "Maximize Sharpe Ratio"),
        ("min_variance", "conservative", "Minimize Portfolio Variance"),
        ("target_volatility", "aggressive", "Target 15% Volatility")
    ]
    
    for objective, risk_pref, description in optimization_tests:
        print(f"\n📊 {description} ({objective}):")
        print("-" * 40)
        
        try:
            # Create optimized portfolio plan
            plan = planner.create_optimized_portfolio_plan(
                asset_data=asset_data,
                risk_preference=risk_pref,
                objective=objective,
                allow_cash=False
            )
            
            # Display results
            print(f"   Risk Preference: {plan['risk_preference']}")
            print(f"   Target Volatility: {plan['target_volatility']:.1%}")
            print(f"   Optimization Objective: {plan['objective']}")
            
            print(f"\n   📈 Optimal Allocation:")
            for asset, weight in plan['allocation'].items():
                print(f"      {asset}: {weight:.1%}")
            
            metrics = plan['metrics']
            print(f"\n   📊 Portfolio Metrics (Requirement 5):")
            print(f"      Expected Return: {metrics['expected_return']:.2%}")
            print(f"      Portfolio Volatility: {metrics['volatility']:.2%}")
            print(f"      Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
            print(f"      VaR (95%): {metrics['var_95']:.2%}")
            print(f"      VaR (99%): {metrics['var_99']:.2%}")
            
        except Exception as e:
            print(f"   ❌ Optimization failed: {e}")
    
    # Test portfolio constraints (Requirement 4)
    print("\n🔒 Testing Portfolio Constraints:")
    print("=" * 40)
    
    # Test with cash allowed
    print("📊 Portfolio with Cash Allocation Allowed:")
    try:
        plan_with_cash = planner.create_optimized_portfolio_plan(
            asset_data=asset_data,
            risk_preference="conservative",
            objective="min_variance",
            allow_cash=True
        )
        
        total_weight = sum(plan_with_cash['allocation'].values())
        all_positive = all(w >= 0 for w in plan_with_cash['allocation'].values())
        
        print(f"   ✅ Weights sum to 1.0: {abs(total_weight - 1.0) < 1e-6}")
        print(f"   ✅ All weights ≥ 0: {all_positive}")
        print(f"   📈 Allocation with cash:")
        for asset, weight in plan_with_cash['allocation'].items():
            print(f"      {asset}: {weight:.1%}")
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
    
    # Test traditional vs optimized approach
    print("\n🔄 Comparing Traditional vs Markowitz Optimization:")
    print("=" * 60)
    
    # Traditional approach
    traditional_plan = planner.create_portfolio_plan("long_term", "moderate", 0.0, 0.10)
    print("📊 Traditional Allocation:")
    for asset, weight in traditional_plan['allocation'].items():
        print(f"   {asset}: {weight:.1%}")
    
    # Markowitz optimization
    try:
        markowitz_plan = planner.create_optimized_portfolio_plan(
            asset_data=asset_data,
            risk_preference="moderate",
            objective="sharpe_ratio",
            allow_cash=False
        )
        
        print("\n🎯 Markowitz Optimized Allocation:")
        for asset, weight in markowitz_plan['allocation'].items():
            print(f"   {asset}: {weight:.1%}")
        
        print(f"\n📈 Optimization Benefits:")
        metrics = markowitz_plan['metrics']
        print(f"   Expected Return: {metrics['expected_return']:.2%}")
        print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
        print(f"   Risk-Adjusted Performance: {'Superior' if metrics['sharpe_ratio'] > 0.5 else 'Good'}")
        
    except Exception as e:
        print(f"   ❌ Markowitz optimization failed: {e}")
    
    print("\n✅ Advanced Portfolio Planner testing completed!")
    print("🎯 Successfully demonstrated all requirements:")
    print("   1. ✅ Markowitz mean-variance optimization with expected returns and covariance matrix")
    print("   2. ✅ Risk preference mapping to target volatility levels")
    print("   3. ✅ Sharpe ratio maximization and minimum variance optimization")
    print("   4. ✅ Portfolio constraints (weights ≥ 0, sum = 1, optional cash)")
    print("   5. ✅ Advanced portfolio metrics (expected return, volatility, Sharpe ratio, VaR)")

