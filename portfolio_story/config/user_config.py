"""
User Configuration System for AI Portfolio Management

This module provides comprehensive user configuration management, allowing users
to customize asset selection, risk preferences, optimization parameters, and
other portfolio management settings.

Key Features:
- Asset universe customization and management
- Risk preference configuration
- Optimization parameter settings
- User-specific constraints and preferences
- Validation and error handling for all configurations
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import pandas as pd
from enum import Enum

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """Risk level enumeration for user preferences."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"

class AssetClass(Enum):
    """Asset class enumeration for portfolio construction."""
    EQUITIES = "equities"
    BONDS = "bonds"
    COMMODITIES = "commodities"
    CRYPTOCURRENCY = "cryptocurrency"
    REAL_ESTATE = "real_estate"
    CASH = "cash"
    ALTERNATIVES = "alternatives"

@dataclass
class AssetConfig:
    """Configuration for individual assets."""
    symbol: str
    name: str
    asset_class: AssetClass
    exchange: str
    currency: str
    min_weight: float = 0.0
    max_weight: float = 1.0
    enabled: bool = True
    custom_volatility: Optional[float] = None
    custom_correlation: Optional[Dict[str, float]] = None

@dataclass
class RiskConfig:
    """Risk management configuration."""
    risk_level: RiskLevel
    target_volatility: float
    max_single_asset_weight: float = 0.4
    max_asset_class_weight: float = 0.7
    min_diversification_ratio: float = 0.3
    max_drawdown_limit: float = 0.25
    var_confidence_level: float = 0.95
    rebalancing_frequency: str = "monthly"  # daily, weekly, monthly, quarterly
    rebalancing_threshold: float = 0.05  # 5% drift threshold

@dataclass
class OptimizationConfig:
    """Portfolio optimization configuration."""
    optimization_method: str = "markowitz"  # markowitz, black_litterman, risk_parity
    objective: str = "sharpe_ratio"  # sharpe_ratio, min_variance, max_return, target_volatility
    transaction_costs: float = 0.001  # 0.1% transaction cost
    turnover_limit: float = 0.3  # Maximum 30% turnover per rebalance
    allow_short_selling: bool = False
    allow_leverage: bool = False
    max_leverage: float = 1.0
    lookback_period: int = 252  # Trading days for historical data
    estimation_method: str = "sample"  # sample, shrinkage, robust

@dataclass
class UserPreferences:
    """User-specific preferences and constraints."""
    preferred_asset_classes: List[AssetClass]
    excluded_assets: List[str] = None
    esg_preferences: bool = False
    sector_preferences: Dict[str, float] = None
    geographic_preferences: Dict[str, float] = None
    liquidity_requirements: float = 0.1  # Minimum 10% in liquid assets
    tax_considerations: bool = False
    currency_hedging: bool = False
    base_currency: str = "USD"

@dataclass
class PortfolioConfig:
    """Complete portfolio configuration."""
    user_id: str
    portfolio_name: str
    assets: List[AssetConfig]
    risk_config: RiskConfig
    optimization_config: OptimizationConfig
    user_preferences: UserPreferences
    created_at: str = ""
    updated_at: str = ""
    version: str = "1.0"

class UserConfigManager:
    """
    Comprehensive user configuration management system.
    
    This class handles all aspects of user configuration including:
    - Asset universe management
    - Risk preference configuration
    - Optimization parameter settings
    - Validation and error handling
    - Configuration persistence and loading
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize the User Configuration Manager.
        
        Args:
            config_dir: Directory to store configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.default_assets = self._load_default_assets()
        self.risk_mappings = self._get_risk_mappings()
        
    def create_portfolio_config(self, 
                              user_id: str,
                              portfolio_name: str,
                              risk_level: RiskLevel,
                              preferred_assets: Optional[List[str]] = None,
                              custom_settings: Optional[Dict[str, Any]] = None) -> PortfolioConfig:
        """
        Create a new portfolio configuration.
        
        Args:
            user_id: Unique user identifier
            portfolio_name: Name for the portfolio
            risk_level: Risk level preference
            preferred_assets: List of preferred asset symbols
            custom_settings: Custom configuration overrides
            
        Returns:
            Complete portfolio configuration
        """
        try:
            # Get risk configuration
            risk_config = self._create_risk_config(risk_level, custom_settings)
            
            # Get asset configuration
            assets = self._create_asset_config(preferred_assets, custom_settings)
            
            # Get optimization configuration
            optimization_config = self._create_optimization_config(risk_level, custom_settings)
            
            # Get user preferences
            user_preferences = self._create_user_preferences(preferred_assets, custom_settings)
            
            # Create portfolio configuration
            config = PortfolioConfig(
                user_id=user_id,
                portfolio_name=portfolio_name,
                assets=assets,
                risk_config=risk_config,
                optimization_config=optimization_config,
                user_preferences=user_preferences,
                created_at=pd.Timestamp.now().isoformat(),
                updated_at=pd.Timestamp.now().isoformat()
            )
            
            # Validate configuration
            self._validate_config(config)
            
            logger.info(f"Created portfolio configuration for user {user_id}: {portfolio_name}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to create portfolio configuration: {e}")
            raise
    
    def save_config(self, config: PortfolioConfig) -> bool:
        """
        Save portfolio configuration to file.
        
        Args:
            config: Portfolio configuration to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            config.updated_at = pd.Timestamp.now().isoformat()
            filename = f"{config.user_id}_{config.portfolio_name}.json"
            filepath = self.config_dir / filename
            
            # Convert to dictionary and save
            config_dict = asdict(config)
            with open(filepath, 'w') as f:
                json.dump(config_dict, f, indent=2, default=str)
            
            logger.info(f"Saved configuration to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def load_config(self, user_id: str, portfolio_name: str) -> Optional[PortfolioConfig]:
        """
        Load portfolio configuration from file.
        
        Args:
            user_id: User identifier
            portfolio_name: Portfolio name
            
        Returns:
            Portfolio configuration or None if not found
        """
        try:
            filename = f"{user_id}_{portfolio_name}.json"
            filepath = self.config_dir / filename
            
            if not filepath.exists():
                logger.warning(f"Configuration file not found: {filepath}")
                return None
            
            with open(filepath, 'r') as f:
                config_dict = json.load(f)
            
            # Convert back to PortfolioConfig
            config = self._dict_to_config(config_dict)
            
            logger.info(f"Loaded configuration from {filepath}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return None
    
    def get_available_assets(self, 
                           asset_class: Optional[AssetClass] = None,
                           exchange: Optional[str] = None,
                           currency: Optional[str] = None) -> List[AssetConfig]:
        """
        Get list of available assets based on filters.
        
        Args:
            asset_class: Filter by asset class
            exchange: Filter by exchange
            currency: Filter by currency
            
        Returns:
            List of available assets
        """
        assets = self.default_assets.copy()
        
        if asset_class:
            assets = [a for a in assets if a.asset_class == asset_class]
        
        if exchange:
            assets = [a for a in assets if a.exchange == exchange]
            
        if currency:
            assets = [a for a in assets if a.currency == currency]
        
        return assets
    
    def add_custom_asset(self, 
                        symbol: str,
                        name: str,
                        asset_class: AssetClass,
                        exchange: str,
                        currency: str = "USD",
                        volatility: Optional[float] = None) -> AssetConfig:
        """
        Add a custom asset to the available assets list.
        
        Args:
            symbol: Asset symbol
            name: Asset name
            asset_class: Asset class
            exchange: Exchange
            currency: Currency
            volatility: Custom volatility estimate
            
        Returns:
            Asset configuration
        """
        asset = AssetConfig(
            symbol=symbol,
            name=name,
            asset_class=asset_class,
            exchange=exchange,
            currency=currency,
            custom_volatility=volatility
        )
        
        # Add to default assets if not already present
        if not any(a.symbol == symbol for a in self.default_assets):
            self.default_assets.append(asset)
            logger.info(f"Added custom asset: {symbol} ({name})")
        
        return asset
    
    def _create_risk_config(self, risk_level: RiskLevel, custom_settings: Optional[Dict]) -> RiskConfig:
        """Create risk configuration based on risk level."""
        base_config = self.risk_mappings[risk_level]
        
        # Apply custom settings if provided
        if custom_settings and 'risk' in custom_settings:
            base_config.update(custom_settings['risk'])
        
        return RiskConfig(**base_config)
    
    def _create_asset_config(self, preferred_assets: Optional[List[str]], custom_settings: Optional[Dict]) -> List[AssetConfig]:
        """Create asset configuration."""
        if preferred_assets:
            # Filter assets based on preferences
            assets = [a for a in self.default_assets if a.symbol in preferred_assets]
        else:
            # Use default diversified set
            assets = self._get_default_diversified_assets()
        
        # Apply custom settings
        if custom_settings and 'assets' in custom_settings:
            for asset in assets:
                if asset.symbol in custom_settings['assets']:
                    asset_settings = custom_settings['assets'][asset.symbol]
                    for key, value in asset_settings.items():
                        if hasattr(asset, key):
                            setattr(asset, key, value)
        
        return assets
    
    def _create_optimization_config(self, risk_level: RiskLevel, custom_settings: Optional[Dict]) -> OptimizationConfig:
        """Create optimization configuration."""
        base_config = {
            'optimization_method': 'markowitz',
            'objective': 'sharpe_ratio',
            'transaction_costs': 0.001,
            'turnover_limit': 0.3,
            'allow_short_selling': False,
            'allow_leverage': False,
            'max_leverage': 1.0,
            'lookback_period': 252,
            'estimation_method': 'sample'
        }
        
        # Adjust for risk level
        if risk_level == RiskLevel.CONSERVATIVE:
            base_config['objective'] = 'min_variance'
            base_config['turnover_limit'] = 0.2
        elif risk_level == RiskLevel.AGGRESSIVE:
            base_config['allow_leverage'] = True
            base_config['max_leverage'] = 1.5
        
        # Apply custom settings
        if custom_settings and 'optimization' in custom_settings:
            base_config.update(custom_settings['optimization'])
        
        return OptimizationConfig(**base_config)
    
    def _create_user_preferences(self, preferred_assets: Optional[List[str]], custom_settings: Optional[Dict]) -> UserPreferences:
        """Create user preferences configuration."""
        # Determine preferred asset classes from preferred assets
        preferred_classes = []
        if preferred_assets:
            for asset in self.default_assets:
                if asset.symbol in preferred_assets and asset.asset_class not in preferred_classes:
                    preferred_classes.append(asset.asset_class)
        else:
            preferred_classes = list(AssetClass)
        
        base_preferences = {
            'preferred_asset_classes': preferred_classes,
            'excluded_assets': [],
            'esg_preferences': False,
            'sector_preferences': {},
            'geographic_preferences': {},
            'liquidity_requirements': 0.1,
            'tax_considerations': False,
            'currency_hedging': False,
            'base_currency': 'USD'
        }
        
        # Apply custom settings
        if custom_settings and 'preferences' in custom_settings:
            base_preferences.update(custom_settings['preferences'])
        
        return UserPreferences(**base_preferences)
    
    def _validate_config(self, config: PortfolioConfig) -> bool:
        """Validate portfolio configuration."""
        errors = []
        
        # Validate assets
        if not config.assets:
            errors.append("No assets configured")
        
        # Validate weights sum to reasonable range
        total_weight = sum(asset.max_weight for asset in config.assets if asset.enabled)
        if total_weight < 0.5:
            errors.append("Total available asset weights too low")
        
        # Validate risk configuration
        if config.risk_config.target_volatility <= 0 or config.risk_config.target_volatility > 1:
            errors.append("Invalid target volatility")
        
        # Validate optimization configuration
        if config.optimization_config.max_leverage < 1.0:
            errors.append("Maximum leverage must be >= 1.0")
        
        if errors:
            error_msg = "; ".join(errors)
            logger.error(f"Configuration validation failed: {error_msg}")
            raise ValueError(f"Invalid configuration: {error_msg}")
        
        return True
    
    def _load_default_assets(self) -> List[AssetConfig]:
        """Load default asset universe."""
        return [
            # Equities
            AssetConfig("SPY", "SPDR S&P 500 ETF", AssetClass.EQUITIES, "NYSE", "USD"),
            AssetConfig("QQQ", "Invesco QQQ Trust", AssetClass.EQUITIES, "NASDAQ", "USD"),
            AssetConfig("VTI", "Vanguard Total Stock Market ETF", AssetClass.EQUITIES, "NYSE", "USD"),
            AssetConfig("VEA", "Vanguard FTSE Developed Markets ETF", AssetClass.EQUITIES, "NYSE", "USD"),
            AssetConfig("VWO", "Vanguard FTSE Emerging Markets ETF", AssetClass.EQUITIES, "NYSE", "USD"),
            
            # Bonds
            AssetConfig("BND", "Vanguard Total Bond Market ETF", AssetClass.BONDS, "NASDAQ", "USD"),
            AssetConfig("TLT", "iShares 20+ Year Treasury Bond ETF", AssetClass.BONDS, "NASDAQ", "USD"),
            AssetConfig("LQD", "iShares iBoxx $ Investment Grade Corporate Bond ETF", AssetClass.BONDS, "NASDAQ", "USD"),
            AssetConfig("HYG", "iShares iBoxx $ High Yield Corporate Bond ETF", AssetClass.BONDS, "NASDAQ", "USD"),
            
            # Commodities
            AssetConfig("GLD", "SPDR Gold Trust", AssetClass.COMMODITIES, "NYSE", "USD"),
            AssetConfig("SLV", "iShares Silver Trust", AssetClass.COMMODITIES, "NYSE", "USD"),
            AssetConfig("DJP", "iPath Bloomberg Commodity Index Total Return ETN", AssetClass.COMMODITIES, "NYSE", "USD"),
            
            # Cryptocurrency
            AssetConfig("GBTC", "Grayscale Bitcoin Trust", AssetClass.CRYPTOCURRENCY, "OTC", "USD"),
            AssetConfig("ETHE", "Grayscale Ethereum Trust", AssetClass.CRYPTOCURRENCY, "OTC", "USD"),
            
            # Cash
            AssetConfig("SHY", "iShares 1-3 Year Treasury Bond ETF", AssetClass.CASH, "NASDAQ", "USD"),
            AssetConfig("BIL", "SPDR Bloomberg Barclays 1-3 Month T-Bill ETF", AssetClass.CASH, "NYSE", "USD"),
        ]
    
    def _get_risk_mappings(self) -> Dict[RiskLevel, Dict]:
        """Get risk level mappings to configuration parameters."""
        return {
            RiskLevel.CONSERVATIVE: {
                'risk_level': RiskLevel.CONSERVATIVE,
                'target_volatility': 0.05,
                'max_single_asset_weight': 0.3,
                'max_asset_class_weight': 0.6,
                'min_diversification_ratio': 0.4,
                'max_drawdown_limit': 0.15,
                'var_confidence_level': 0.99,
                'rebalancing_frequency': 'quarterly',
                'rebalancing_threshold': 0.03
            },
            RiskLevel.MODERATE: {
                'risk_level': RiskLevel.MODERATE,
                'target_volatility': 0.10,
                'max_single_asset_weight': 0.4,
                'max_asset_class_weight': 0.7,
                'min_diversification_ratio': 0.3,
                'max_drawdown_limit': 0.25,
                'var_confidence_level': 0.95,
                'rebalancing_frequency': 'monthly',
                'rebalancing_threshold': 0.05
            },
            RiskLevel.AGGRESSIVE: {
                'risk_level': RiskLevel.AGGRESSIVE,
                'target_volatility': 0.15,
                'max_single_asset_weight': 0.5,
                'max_asset_class_weight': 0.8,
                'min_diversification_ratio': 0.2,
                'max_drawdown_limit': 0.35,
                'var_confidence_level': 0.90,
                'rebalancing_frequency': 'weekly',
                'rebalancing_threshold': 0.08
            },
            RiskLevel.CUSTOM: {
                'risk_level': RiskLevel.CUSTOM,
                'target_volatility': 0.10,
                'max_single_asset_weight': 0.4,
                'max_asset_class_weight': 0.7,
                'min_diversification_ratio': 0.3,
                'max_drawdown_limit': 0.25,
                'var_confidence_level': 0.95,
                'rebalancing_frequency': 'monthly',
                'rebalancing_threshold': 0.05
            }
        }
    
    def _get_default_diversified_assets(self) -> List[AssetConfig]:
        """Get default diversified asset set."""
        return [
            asset for asset in self.default_assets 
            if asset.symbol in ["SPY", "VEA", "BND", "GLD", "SHY"]
        ]
    
    def _dict_to_config(self, config_dict: Dict) -> PortfolioConfig:
        """Convert dictionary back to PortfolioConfig object."""
        # Convert assets
        assets = []
        for asset_dict in config_dict['assets']:
            asset_dict['asset_class'] = AssetClass(asset_dict['asset_class'])
            assets.append(AssetConfig(**asset_dict))
        
        # Convert risk config
        risk_dict = config_dict['risk_config']
        risk_dict['risk_level'] = RiskLevel(risk_dict['risk_level'])
        risk_config = RiskConfig(**risk_dict)
        
        # Convert optimization config
        optimization_config = OptimizationConfig(**config_dict['optimization_config'])
        
        # Convert user preferences
        pref_dict = config_dict['user_preferences']
        pref_dict['preferred_asset_classes'] = [AssetClass(ac) for ac in pref_dict['preferred_asset_classes']]
        user_preferences = UserPreferences(**pref_dict)
        
        return PortfolioConfig(
            user_id=config_dict['user_id'],
            portfolio_name=config_dict['portfolio_name'],
            assets=assets,
            risk_config=risk_config,
            optimization_config=optimization_config,
            user_preferences=user_preferences,
            created_at=config_dict.get('created_at', ''),
            updated_at=config_dict.get('updated_at', ''),
            version=config_dict.get('version', '1.0')
        )

# Example usage and testing
if __name__ == "__main__":
    # Initialize configuration manager
    config_manager = UserConfigManager()
    
    print("=== AI Portfolio Configuration System Demo ===\n")
    
    # 1. Create a portfolio configuration
    print("1. CREATING PORTFOLIO CONFIGURATION")
    print("-" * 50)
    
    portfolio_config = config_manager.create_portfolio_config(
        user_id="user123",
        portfolio_name="My Diversified Portfolio",
        risk_level=RiskLevel.MODERATE,
        preferred_assets=["SPY", "VEA", "BND", "GLD", "SHY"]
    )
    
    print(f"Created portfolio: {portfolio_config.portfolio_name}")
    print(f"Risk level: {portfolio_config.risk_config.risk_level.value}")
    print(f"Target volatility: {portfolio_config.risk_config.target_volatility:.1%}")
    print(f"Number of assets: {len(portfolio_config.assets)}")
    
    # 2. Save configuration
    print("\n2. SAVING CONFIGURATION")
    print("-" * 50)
    success = config_manager.save_config(portfolio_config)
    print(f"Configuration saved: {success}")
    
    # 3. Load configuration
    print("\n3. LOADING CONFIGURATION")
    print("-" * 50)
    loaded_config = config_manager.load_config("user123", "My Diversified Portfolio")
    if loaded_config:
        print(f"Loaded portfolio: {loaded_config.portfolio_name}")
        print(f"Assets: {[asset.symbol for asset in loaded_config.assets]}")
    
    # 4. Get available assets
    print("\n4. AVAILABLE ASSETS BY CLASS")
    print("-" * 50)
    for asset_class in AssetClass:
        assets = config_manager.get_available_assets(asset_class=asset_class)
        print(f"{asset_class.value.title()}: {len(assets)} assets")
        if assets:
            print(f"  Examples: {', '.join([a.symbol for a in assets[:3]])}")
    
    # 5. Add custom asset
    print("\n5. ADDING CUSTOM ASSET")
    print("-" * 50)
    custom_asset = config_manager.add_custom_asset(
        symbol="TSLA",
        name="Tesla Inc.",
        asset_class=AssetClass.EQUITIES,
        exchange="NASDAQ",
        currency="USD",
        volatility=0.35
    )
    print(f"Added custom asset: {custom_asset.symbol} ({custom_asset.name})")
    
    print("\n=== Configuration System Demo Complete ===")
    print("The system is now ready for user-customized portfolio management!")
