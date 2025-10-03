"""
Comprehensive Validation Framework for AI Portfolio Management System

This module provides robust validation for all inputs, calculations, and data
throughout the portfolio management system to ensure reliability and accuracy.

Key Features:
- Input validation for all user inputs and configurations
- Data quality checks for market data and calculations
- Portfolio constraint validation
- Risk parameter validation
- Optimization result validation
- Cross-validation between components
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union, Tuple
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import warnings

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

class ValidationSeverity(Enum):
    """Validation severity levels."""
    ERROR = "error"      # Must fix - system cannot proceed
    WARNING = "warning"  # Should fix - may cause issues
    INFO = "info"        # Informational - best practice

@dataclass
class ValidationResult:
    """Result of validation check."""
    is_valid: bool
    severity: ValidationSeverity
    message: str
    component: str
    field: Optional[str] = None
    suggested_fix: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class PortfolioValidator:
    """
    Comprehensive validator for portfolio management system.
    
    This class provides validation methods for all aspects of the portfolio
    management system, ensuring data quality, constraint compliance, and
    calculation accuracy.
    """
    
    def __init__(self):
        """Initialize the portfolio validator."""
        self.validation_results = []
        self.error_threshold = 0.05  # 5% error threshold for calculations
        
    def validate_asset_data(self, data: pd.DataFrame, 
                          required_columns: List[str] = None) -> List[ValidationResult]:
        """
        Validate asset market data quality.
        
        Args:
            data: Market data DataFrame
            required_columns: Required column names
            
        Returns:
            List of validation results
        """
        results = []
        
        if required_columns is None:
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        # Check if data is empty
        if data.empty:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="Asset data is empty",
                component="data_validation",
                field="data_frame"
            ))
            return results
        
        # Check required columns
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message=f"Missing required columns: {missing_columns}",
                component="data_validation",
                field="columns",
                suggested_fix="Ensure data contains all required price and volume columns"
            ))
        
        # Check for sufficient data points
        min_data_points = 30
        if len(data) < min_data_points:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.WARNING,
                message=f"Insufficient data points: {len(data)} < {min_data_points}",
                component="data_validation",
                field="data_length",
                suggested_fix="Use data with at least 30 trading days"
            ))
        
        # Check for missing values
        missing_percentage = data.isnull().sum().sum() / (len(data) * len(data.columns))
        if missing_percentage > 0.1:  # More than 10% missing
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.WARNING,
                message=f"High missing data percentage: {missing_percentage:.1%}",
                component="data_validation",
                field="missing_data",
                suggested_fix="Consider data cleaning or interpolation"
            ))
        
        # Check for unrealistic price values
        for col in ['Open', 'High', 'Low', 'Close']:
            if col in data.columns:
                if (data[col] <= 0).any():
                    results.append(ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Non-positive prices found in {col}",
                        component="data_validation",
                        field=col,
                        suggested_fix="Remove or correct non-positive price data"
                    ))
                
                # Check for extreme price movements (>50% in one day)
                if len(data) > 1:
                    returns = data[col].pct_change().dropna()
                    extreme_moves = abs(returns) > 0.5
                    if extreme_moves.any():
                        results.append(ValidationResult(
                            is_valid=False,
                            severity=ValidationSeverity.WARNING,
                            message=f"Extreme price movements detected in {col}: {extreme_moves.sum()} days",
                            component="data_validation",
                            field=col,
                            suggested_fix="Review data for splits, dividends, or errors"
                        ))
        
        # Check volume data
        if 'Volume' in data.columns:
            if (data['Volume'] < 0).any():
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message="Negative volume data found",
                    component="data_validation",
                    field="Volume",
                    suggested_fix="Correct negative volume values"
                ))
        
        return results
    
    def validate_portfolio_weights(self, weights: Dict[str, float],
                                 max_single_weight: float = 0.4,
                                 min_weight: float = 0.0) -> List[ValidationResult]:
        """
        Validate portfolio weight constraints.
        
        Args:
            weights: Portfolio weights dictionary
            max_single_weight: Maximum weight for single asset
            min_weight: Minimum weight threshold
            
        Returns:
            List of validation results
        """
        results = []
        
        if not weights:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="Portfolio weights are empty",
                component="portfolio_validation",
                field="weights"
            ))
            return results
        
        # Check weight sum
        weight_sum = sum(weights.values())
        if abs(weight_sum - 1.0) > 0.01:  # 1% tolerance
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message=f"Weights do not sum to 1.0: {weight_sum:.6f}",
                component="portfolio_validation",
                field="weight_sum",
                suggested_fix="Normalize weights to sum to 1.0"
            ))
        
        # Check individual weights
        for asset, weight in weights.items():
            if weight < min_weight:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    message=f"Asset {asset} has negative weight: {weight:.6f}",
                    component="portfolio_validation",
                    field=f"weight_{asset}",
                    suggested_fix="Set minimum weight to 0 or remove asset"
                ))
            
            if weight > max_single_weight:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    message=f"Asset {asset} exceeds maximum weight: {weight:.6f} > {max_single_weight}",
                    component="portfolio_validation",
                    field=f"weight_{asset}",
                    suggested_fix=f"Reduce weight to maximum {max_single_weight}"
                ))
        
        return results
    
    def validate_risk_parameters(self, risk_config: Dict[str, Any]) -> List[ValidationResult]:
        """
        Validate risk management parameters.
        
        Args:
            risk_config: Risk configuration dictionary
            
        Returns:
            List of validation results
        """
        results = []
        
        # Validate target volatility
        target_vol = risk_config.get('target_volatility', 0.1)
        if not (0.01 <= target_vol <= 0.5):  # 1% to 50%
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message=f"Target volatility out of range: {target_vol:.3f}",
                component="risk_validation",
                field="target_volatility",
                suggested_fix="Set target volatility between 1% and 50%"
            ))
        
        # Validate VaR confidence level
        var_confidence = risk_config.get('var_confidence_level', 0.95)
        if not (0.9 <= var_confidence <= 0.99):
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.WARNING,
                message=f"VaR confidence level out of recommended range: {var_confidence:.3f}",
                component="risk_validation",
                field="var_confidence_level",
                suggested_fix="Use confidence level between 90% and 99%"
            ))
        
        # Validate drawdown limit
        max_drawdown = risk_config.get('max_drawdown_limit', 0.25)
        if not (0.05 <= max_drawdown <= 0.5):  # 5% to 50%
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.WARNING,
                message=f"Maximum drawdown limit out of range: {max_drawdown:.3f}",
                component="risk_validation",
                field="max_drawdown_limit",
                suggested_fix="Set drawdown limit between 5% and 50%"
            ))
        
        return results
    
    def validate_covariance_matrix(self, cov_matrix: pd.DataFrame) -> List[ValidationResult]:
        """
        Validate covariance matrix properties.
        
        Args:
            cov_matrix: Covariance matrix DataFrame
            
        Returns:
            List of validation results
        """
        results = []
        
        if cov_matrix.empty:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="Covariance matrix is empty",
                component="covariance_validation",
                field="cov_matrix"
            ))
            return results
        
        # Check if matrix is square
        if cov_matrix.shape[0] != cov_matrix.shape[1]:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message=f"Covariance matrix is not square: {cov_matrix.shape}",
                component="covariance_validation",
                field="matrix_shape"
            ))
        
        # Check for NaN values
        if cov_matrix.isnull().any().any():
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="Covariance matrix contains NaN values",
                component="covariance_validation",
                field="nan_values"
            ))
        
        # Check for infinite values
        if np.isinf(cov_matrix.values).any():
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="Covariance matrix contains infinite values",
                component="covariance_validation",
                field="infinite_values"
            ))
        
        # Check symmetry
        if not np.allclose(cov_matrix.values, cov_matrix.values.T, atol=1e-10):
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="Covariance matrix is not symmetric",
                component="covariance_validation",
                field="symmetry"
            ))
        
        # Check positive semi-definiteness
        try:
            eigenvalues = np.linalg.eigvals(cov_matrix.values)
            if np.any(eigenvalues < -1e-10):  # Small tolerance for numerical errors
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Covariance matrix is not positive semi-definite. Min eigenvalue: {eigenvalues.min():.2e}",
                    component="covariance_validation",
                    field="positive_definite",
                    suggested_fix="Use shrinkage estimation or regularization"
                ))
        except np.linalg.LinAlgError:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="Failed to compute eigenvalues of covariance matrix",
                component="covariance_validation",
                field="eigenvalue_computation"
            ))
        
        return results
    
    def validate_expected_returns(self, expected_returns: pd.Series) -> List[ValidationResult]:
        """
        Validate expected returns vector.
        
        Args:
            expected_returns: Expected returns Series
            
        Returns:
            List of validation results
        """
        results = []
        
        if expected_returns.empty:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="Expected returns vector is empty",
                component="returns_validation",
                field="expected_returns"
            ))
            return results
        
        # Check for NaN values
        if expected_returns.isnull().any():
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="Expected returns contain NaN values",
                component="returns_validation",
                field="nan_values"
            ))
        
        # Check for infinite values
        if np.isinf(expected_returns.values).any():
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="Expected returns contain infinite values",
                component="returns_validation",
                field="infinite_values"
            ))
        
        # Check for unrealistic returns
        extreme_returns = abs(expected_returns) > 1.0  # More than 100% annual return
        if extreme_returns.any():
            extreme_assets = expected_returns[extreme_returns].index.tolist()
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.WARNING,
                message=f"Unrealistic expected returns (>100%) for assets: {extreme_assets}",
                component="returns_validation",
                field="extreme_returns",
                suggested_fix="Review return estimation methodology"
            ))
        
        return results
    
    def validate_optimization_result(self, weights: Dict[str, float],
                                   expected_return: float,
                                   volatility: float,
                                   sharpe_ratio: float) -> List[ValidationResult]:
        """
        Validate optimization results for consistency.
        
        Args:
            weights: Optimized portfolio weights
            expected_return: Portfolio expected return
            volatility: Portfolio volatility
            sharpe_ratio: Portfolio Sharpe ratio
            
        Returns:
            List of validation results
        """
        results = []
        
        # Validate weights
        weight_results = self.validate_portfolio_weights(weights)
        results.extend(weight_results)
        
        # Check Sharpe ratio calculation consistency
        if abs(sharpe_ratio - expected_return / volatility) > 1e-6:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message=f"Sharpe ratio inconsistency: {sharpe_ratio:.6f} vs {expected_return/volatility:.6f}",
                component="optimization_validation",
                field="sharpe_ratio"
            ))
        
        # Check for reasonable values
        if volatility <= 0:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message=f"Non-positive volatility: {volatility:.6f}",
                component="optimization_validation",
                field="volatility"
            ))
        
        if abs(expected_return) > 1.0:  # More than 100% annual return
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.WARNING,
                message=f"Unrealistic expected return: {expected_return:.1%}",
                component="optimization_validation",
                field="expected_return"
            ))
        
        return results
    
    def validate_user_config(self, config: Dict[str, Any]) -> List[ValidationResult]:
        """
        Validate user configuration parameters.
        
        Args:
            config: User configuration dictionary
            
        Returns:
            List of validation results
        """
        results = []
        
        # Validate required fields
        required_fields = ['user_id', 'portfolio_name', 'risk_level']
        for field in required_fields:
            if field not in config:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Missing required field: {field}",
                    component="config_validation",
                    field=field
                ))
        
        # Validate risk level
        if 'risk_level' in config:
            valid_risk_levels = ['conservative', 'moderate', 'aggressive', 'custom']
            if config['risk_level'] not in valid_risk_levels:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Invalid risk level: {config['risk_level']}",
                    component="config_validation",
                    field="risk_level",
                    suggested_fix=f"Use one of: {valid_risk_levels}"
                ))
        
        # Validate asset preferences
        if 'preferred_assets' in config:
            if not isinstance(config['preferred_assets'], list):
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message="Preferred assets must be a list",
                    component="config_validation",
                    field="preferred_assets"
                ))
            elif len(config['preferred_assets']) < 2:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    message="Portfolio should have at least 2 assets for diversification",
                    component="config_validation",
                    field="preferred_assets"
                ))
        
        return results
    
    def validate_data_quality(self, data: pd.DataFrame, 
                            data_type: str = "market_data") -> List[ValidationResult]:
        """
        Comprehensive data quality validation.
        
        Args:
            data: Data to validate
            data_type: Type of data being validated
            
        Returns:
            List of validation results
        """
        results = []
        
        if data.empty:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message=f"{data_type} is empty",
                component="data_quality",
                field="empty_data"
            ))
            return results
        
        # Check data freshness
        if 'Date' in data.columns or data.index.name == 'Date':
            if isinstance(data.index, pd.DatetimeIndex):
                latest_date = data.index.max()
                days_old = (pd.Timestamp.now() - latest_date).days
                
                if days_old > 30:
                    results.append(ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.WARNING,
                        message=f"Data is {days_old} days old",
                        component="data_quality",
                        field="data_freshness",
                        suggested_fix="Update data to ensure accuracy"
                    ))
        
        # Check for duplicates
        if data.duplicated().any():
            duplicate_count = data.duplicated().sum()
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.WARNING,
                message=f"Found {duplicate_count} duplicate rows",
                component="data_quality",
                field="duplicates",
                suggested_fix="Remove duplicate entries"
            ))
        
        # Check for constant values (no variation)
        for col in data.select_dtypes(include=[np.number]).columns:
            if data[col].nunique() <= 1:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    message=f"Column {col} has no variation",
                    component="data_quality",
                    field=f"constant_{col}",
                    suggested_fix="Check data source or remove constant columns"
                ))
        
        return results
    
    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """
        Get summary of validation results.
        
        Args:
            results: List of validation results
            
        Returns:
            Validation summary dictionary
        """
        total_results = len(results)
        error_count = sum(1 for r in results if r.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for r in results if r.severity == ValidationSeverity.WARNING)
        info_count = sum(1 for r in results if r.severity == ValidationSeverity.INFO)
        
        is_valid = error_count == 0
        
        return {
            'is_valid': is_valid,
            'total_checks': total_results,
            'errors': error_count,
            'warnings': warning_count,
            'info': info_count,
            'validation_passed': is_valid,
            'critical_issues': error_count > 0,
            'needs_attention': warning_count > 0
        }

# Example usage and testing
if __name__ == "__main__":
    print("=== AI Portfolio Validation Framework Demo ===\n")
    
    # Initialize validator
    validator = PortfolioValidator()
    
    # 1. Test asset data validation
    print("1. TESTING ASSET DATA VALIDATION")
    print("-" * 50)
    
    # Create sample data with issues
    dates = pd.date_range('2023-01-01', periods=50, freq='D')
    sample_data = pd.DataFrame({
        'Open': np.random.uniform(100, 200, 50),
        'High': np.random.uniform(100, 200, 50),
        'Low': np.random.uniform(100, 200, 50),
        'Close': np.random.uniform(100, 200, 50),
        'Volume': np.random.uniform(1000000, 5000000, 50)
    }, index=dates)
    
    # Add some issues
    sample_data.loc[dates[10], 'Close'] = -50  # Negative price
    sample_data.loc[dates[20:25], 'Volume'] = np.nan  # Missing volume
    
    results = validator.validate_asset_data(sample_data)
    for result in results:
        print(f"{result.severity.value.upper()}: {result.message}")
    
    # 2. Test portfolio weights validation
    print("\n2. TESTING PORTFOLIO WEIGHTS VALIDATION")
    print("-" * 50)
    
    weights = {'SPY': 0.6, 'BND': 0.5, 'GLD': -0.1}  # Sum > 1, negative weight
    results = validator.validate_portfolio_weights(weights)
    for result in results:
        print(f"{result.severity.value.upper()}: {result.message}")
    
    # 3. Test risk parameters validation
    print("\n3. TESTING RISK PARAMETERS VALIDATION")
    print("-" * 50)
    
    risk_config = {
        'target_volatility': 0.8,  # Too high
        'var_confidence_level': 0.5,  # Too low
        'max_drawdown_limit': 0.8  # Too high
    }
    results = validator.validate_risk_parameters(risk_config)
    for result in results:
        print(f"{result.severity.value.upper()}: {result.message}")
    
    # 4. Test covariance matrix validation
    print("\n4. TESTING COVARIANCE MATRIX VALIDATION")
    print("-" * 50)
    
    # Create invalid covariance matrix
    invalid_cov = pd.DataFrame({
        'SPY': [0.04, 0.02, 0.03],
        'BND': [0.02, 0.01, 0.02],
        'GLD': [0.03, 0.02, 0.05]
    }, index=['SPY', 'BND', 'GLD'])
    
    results = validator.validate_covariance_matrix(invalid_cov)
    for result in results:
        print(f"{result.severity.value.upper()}: {result.message}")
    
    # 5. Test validation summary
    print("\n5. VALIDATION SUMMARY")
    print("-" * 50)
    all_results = validator.validate_asset_data(sample_data)
    summary = validator.get_validation_summary(all_results)
    print(f"Validation passed: {summary['is_valid']}")
    print(f"Total checks: {summary['total_checks']}")
    print(f"Errors: {summary['errors']}, Warnings: {summary['warnings']}")
    
    print("\n=== Validation Framework Demo Complete ===")
    print("The validation system is ready to ensure data quality and reliability!")
