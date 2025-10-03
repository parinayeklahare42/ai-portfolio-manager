"""
The Portfolio Story - Enhanced AI Portfolio Management System
============================================================

This is the central orchestrator of the AI-powered portfolio management system.
It coordinates all components to create, analyze, and manage investment portfolios
using advanced machine learning techniques with comprehensive validation, logging,
and user configuration management.

Key Responsibilities:
- Orchestrates the entire portfolio creation workflow with enhanced reliability
- Coordinates data fetching, analysis, and risk management with validation
- Manages user configurations and asset universe customization
- Provides comprehensive logging and audit trails
- Implements robust error handling and data quality checks
- Supports user-specific portfolio preferences and constraints

Author: parinayeklahare42
Course: 125882 AI in Investment and Risk Management
Assignment: Assessment 2 Hackathon and Coding Challenge
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime, timedelta
import traceback

# Import all system components
from .data.librarian import Librarian
from .models.research_crew import ResearchCrew
from .models.planner import Planner
from .models.selector import Selector
from .safety.safety_officer import SafetyOfficer
from .safety.risk_manager import RiskManager
from .utils.shopkeeper import Shopkeeper
from .utils.caretaker import Caretaker

# Import new enhanced systems
from .config.user_config import UserConfigManager, PortfolioConfig, RiskLevel
from .utils.logging_config import get_logger, get_audit_logger, log_function_performance
from .utils.validation import PortfolioValidator, ValidationError

# Setup enhanced logging
logger = get_logger('portfolio_manager')
audit_logger = get_audit_logger()

class PortfolioManager:
    """
    The main Portfolio Manager orchestrates all components of the AI portfolio system.
    
    This class serves as the central coordinator for the entire portfolio management workflow,
    bringing together all specialized components to create intelligent, risk-managed portfolios.
    
    Component Architecture:
    1. The Librarian - Fetches and caches market data from Yahoo Finance
    2. The Research Crew - Performs AI/ML analysis (momentum, volatility, sentiment)
    3. The Planner - Creates optimal asset allocation strategies
    4. The Selector - Selects specific assets based on ML rankings
    5. The Safety Officer - Applies risk management guardrails
    6. The Risk Manager - Calculates advanced risk metrics (VaR, CVaR)
    7. The Shopkeeper - Creates trade execution orders
    8. The Caretaker - Handles portfolio rebalancing and maintenance
    
    The system uses a modular approach where each component has a specific responsibility,
    making the code maintainable and allowing for easy testing and enhancement.
    """
    
    def __init__(self, config_dir: str = "config", log_dir: str = "logs"):
        """
        Initialize the Enhanced Portfolio Manager with all required components.
        
        Args:
            config_dir: Directory for user configuration files
            log_dir: Directory for log files
            
        This constructor sets up the entire enhanced system with validation,
        logging, and user configuration management capabilities.
        """
        logger.info("Initializing Enhanced AI Portfolio Management System...")
        
        try:
            # Initialize enhanced systems first
            self.config_manager = UserConfigManager(config_dir)
            self.validator = PortfolioValidator()
            
            # Initialize all AI/ML components with enhanced capabilities
            self.librarian = Librarian()          # Data fetching and caching with validation
            self.research_crew = ResearchCrew()    # AI/ML analysis engine with logging
            self.planner = Planner()              # Asset allocation with Markowitz optimization
            self.selector = Selector()            # Asset selection with user preferences
            self.safety_officer = SafetyOfficer() # Risk management guardrails
            self.risk_manager = RiskManager()     # Advanced risk analytics and stress testing
            self.shopkeeper = Shopkeeper()        # Trade execution system
            self.caretaker = Caretaker()          # Portfolio maintenance with user settings
            
            # Enhanced portfolio state tracking
            self.current_portfolio = None         # Currently active portfolio
            self.last_rebalance_date = None        # Last rebalancing date
            self.user_configs = {}                # User configuration cache
            self.performance_metrics = {}         # System performance tracking
            self.validation_results = {}          # Validation history
            
            # System health monitoring
            self.component_status = {
                'librarian': 'active',
                'research_crew': 'active',
                'planner': 'active',
                'selector': 'active',
                'safety_officer': 'active',
                'risk_manager': 'active',
                'shopkeeper': 'active',
                'caretaker': 'active',
                'config_manager': 'active',
                'validator': 'active'
            }
            
            # Log system initialization
            audit_logger.log_system_action("system_initialization", "portfolio_manager",
                                         config_dir=config_dir, log_dir=log_dir)
            
            logger.info("Enhanced AI Portfolio Management System initialized successfully")
            
        except Exception as e:
            logger.critical("Failed to initialize Portfolio Management System", exception=e)
            raise
    
    def create_portfolio(self, time_horizon: str, budget: float, 
                        risk_budget: float = 0.10, sleep_better_dial: float = 0.0,
                        risk_profile: str = "moderate") -> Dict:
        """
        Create a new AI-optimized portfolio based on user requirements.
        
        This is the main method that orchestrates the entire portfolio creation workflow,
        using advanced machine learning techniques to analyze assets, optimize allocation,
        and manage risk according to modern portfolio theory principles.
        
        The process follows an 8-step workflow:
        1. Data Fetching - Get real-time market data from Yahoo Finance
        2. AI Analysis - Use ML algorithms to score and rank assets
        3. Allocation Planning - Create optimal asset allocation strategy
        4. Asset Selection - Choose specific assets based on ML rankings
        5. Safety Checks - Apply risk management guardrails
        6. Risk Management - Calculate advanced risk metrics
        7. Trade Execution - Create detailed buy orders
        8. Portfolio Summary - Compile comprehensive results
        
        Args:
            time_horizon (str): Investment time horizon
                - 'short_term': 1-2 years (higher equity allocation)
                - 'medium_term': 3-5 years (balanced allocation)
                - 'long_term': 5+ years (diversified allocation)
            budget (float): Total investment amount in dollars
            risk_budget (float): Target portfolio volatility (0.10 = 10% annual volatility)
            sleep_better_dial (float): Risk adjustment factor (0-1)
                - 0.0 = No adjustment (use default risk profile)
                - 0.5 = Moderate risk reduction
                - 1.0 = Maximum risk reduction (most conservative)
            risk_profile (str): Base risk tolerance
                - 'conservative': Lower risk, stable returns
                - 'moderate': Balanced risk-return profile
                - 'aggressive': Higher risk, potential for higher returns
                
        Returns:
            Dict: Complete portfolio dictionary containing:
                - portfolio_id: Unique identifier
                - parameters: User inputs and settings
                - market_summary: Current market conditions
                - allocation_plan: Asset allocation strategy
                - analysis_results: ML analysis results for all assets
                - selected_assets: Chosen assets with weights
                - safety_results: Risk management outcomes
                - risk_report: Advanced risk metrics (VaR, CVaR, etc.)
                - buy_list: Detailed trade execution orders
                - execution_summary: Trade summary and costs
                
        Raises:
            Exception: If portfolio creation fails at any step
        """
        logger.info(f"Creating portfolio: {time_horizon}, ${budget:,.2f}, risk={risk_budget:.1%}")
        
        try:
            # Step 1: Data Fetching (The Librarian)
            # Fetch real-time market data from Yahoo Finance with intelligent caching
            logger.info("Step 1: Fetching market data...")
            all_data = self.librarian.get_all_data()  # Get data for all asset classes
            market_summary = self.librarian.get_market_summary()  # Get market context
            
            # Step 2: AI/ML Analysis (The Research Crew)
            # Use machine learning algorithms to analyze and score all assets
            logger.info("Step 2: Analyzing assets...")
            analysis_results = {}
            for asset_class, data_dict in all_data.items():
                if data_dict:  # Only analyze if we have data
                    # Perform comprehensive ML analysis on each asset class
                    analysis_results[asset_class] = self.research_crew.analyze_asset_class(
                        asset_class, data_dict
                    )
            
            # Step 3: Allocation Planning (The Planner)
            # Create optimal asset allocation strategy using new specification logic
            logger.info("Step 3: Creating allocation plan...")
            
            if risk_profile == "new_allocation_system":
                # Use the new 1-5 risk level allocation system
                risk_level = int(sleep_better_dial)
                horizon_map = {
                    'short_term': 'short',
                    'medium_term': 'medium',
                    'long_term': 'long'
                }
                horizon = horizon_map.get(time_horizon, 'medium')
                
                # Create optimal allocation using new logic
                optimal_result = self.planner.create_optimal_allocation(
                    capital=budget,
                    horizon=horizon,
                    risk_level=risk_level,
                    max_vol_pct=risk_budget * 100  # Convert to percentage
                )
                
                # Convert to the expected format
                allocation_plan = {
                    'allocation': optimal_result['weights'],
                    'predicted_vol_pct': optimal_result['predicted_vol_pct'],
                    'risk_status': optimal_result['risk_status'],
                    'assets_selected': optimal_result['assets_selected']
                }
                logger.info(f"New allocation system result: {allocation_plan}")
            else:
                # Use legacy system for backward compatibility
                allocation_plan = self.planner.create_portfolio_plan(
                    time_horizon, risk_profile, sleep_better_dial, risk_budget
                )
            
            # Step 4: Asset Selection (The Selector)
            # Choose specific assets based on ML rankings and allocation targets
            logger.info("Step 4: Selecting assets...")
            selected_assets = self.selector.create_portfolio_selection(
                analysis_results, allocation_plan['allocation']
            )
            
            # Step 5: Safety Checks (The Safety Officer)
            # Apply risk management guardrails and safety measures
            logger.info("Step 5: Running safety checks...")
            safety_results = self.safety_officer.run_safety_checks(
                allocation_plan['allocation'],
                selected_assets,
                sleep_better_dial
            )
            
            # Step 6: Risk Management (The Risk Manager)
            # Calculate advanced risk metrics including VaR, CVaR, and stress testing
            logger.info("Step 6: Managing risk...")
            risk_report = self.risk_manager.generate_risk_report(
                safety_results['final_allocation'], risk_budget
            )
            
            # Step 7: Trade Execution (The Shopkeeper)
            # Create detailed buy orders and calculate trade quantities
            logger.info("Step 7: Creating buy list...")
            dollar_amounts = self.shopkeeper.calculate_dollar_amounts(
                safety_results['final_allocation'], budget
            )
            trade_orders = self.shopkeeper.calculate_share_quantities(
                selected_assets, dollar_amounts
            )
            buy_list = self.shopkeeper.create_buy_list(trade_orders, budget)
            
            # Step 8: Portfolio Summary
            # Compile all results into a comprehensive portfolio dictionary
            portfolio = {
                'portfolio_id': f"PS_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'created_at': datetime.now().isoformat(),
                'parameters': {
                    'time_horizon': time_horizon,
                    'budget': budget,
                    'risk_budget': risk_budget,
                    'sleep_better_dial': sleep_better_dial,
                    'risk_profile': risk_profile
                },
                'market_summary': market_summary,
                'allocation_plan': allocation_plan,
                'analysis_results': analysis_results,
                'selected_assets': selected_assets,
                'safety_results': safety_results,
                'risk_report': risk_report,
                'buy_list': buy_list,
                'execution_summary': self.shopkeeper.create_execution_summary(buy_list)
            }
            
            # Store current portfolio for future operations
            self.current_portfolio = portfolio
            
            logger.info("Portfolio creation completed successfully")
            return portfolio
            
        except Exception as e:
            logger.error(f"Portfolio creation failed: {e}")
            raise
    
    def get_portfolio_summary(self, portfolio: Dict) -> str:
        """
        Create a comprehensive, human-readable portfolio summary.
        
        This method formats all portfolio information into a clear, structured summary
        that includes key metrics, allocation details, risk analysis, and recommendations.
        The summary is designed for easy reading and understanding by both technical
        and non-technical users.
        
        Args:
            portfolio (Dict): Complete portfolio dictionary from create_portfolio()
            
        Returns:
            str: Formatted summary string with:
                - Portfolio identification and parameters
                - Market context and conditions
                - Asset allocation breakdown
                - Risk metrics and analysis
                - Buy list summary
                - Safety messages and recommendations
        """
        summary = []
        summary.append("=" * 60)
        summary.append("THE PORTFOLIO STORY - PORTFOLIO SUMMARY")
        summary.append("=" * 60)
        
        # Basic info
        params = portfolio['parameters']
        summary.append(f"Portfolio ID: {portfolio['portfolio_id']}")
        summary.append(f"Created: {portfolio['created_at']}")
        summary.append(f"Time Horizon: {params['time_horizon']}")
        summary.append(f"Budget: ${params['budget']:,.2f}")
        summary.append(f"Risk Budget: {params['risk_budget']:.1%}")
        summary.append(f"Sleep-Better Dial: {params['sleep_better_dial']:.1f}")
        summary.append("")
        
        # Market context
        market = portfolio['market_summary']
        if 'error' not in market:
            summary.append("MARKET CONTEXT:")
            summary.append(f"ASX 200: {market.get('asx200_close', 0):,.0f} ({market.get('asx200_change_pct', 0):+.1f}%)")
            summary.append("")
        
        # Allocation
        allocation = portfolio['allocation_plan']['allocation']
        summary.append("ASSET ALLOCATION:")
        for asset_class, weight in allocation.items():
            if weight > 0:
                summary.append(f"  {asset_class.title()}: {weight:.1%}")
        summary.append("")
        
        # Risk metrics
        risk = portfolio['risk_report']
        summary.append("RISK METRICS:")
        summary.append(f"  Portfolio Volatility: {risk['portfolio_volatility']:.1%}")
        summary.append(f"  Target Volatility: {risk['target_volatility']:.1%}")
        summary.append(f"  Within Risk Budget: {'Yes' if risk['within_risk_budget'] else 'No'}")
        summary.append(f"  Risk Score: {risk['risk_score']:.2f}")
        summary.append("")
        
        # Buy list
        buy_list = portfolio['buy_list']
        summary.append("BUY LIST:")
        summary.append(f"  Total Spent: ${buy_list['summary']['total_spent']:,.2f}")
        summary.append(f"  Leftover Cash: ${buy_list['summary']['total_leftover']:,.2f}")
        summary.append(f"  Number of Assets: {buy_list['summary']['num_assets']}")
        summary.append("")
        
        # Safety messages
        safety = portfolio['safety_results']
        if safety['messages']:
            summary.append("SAFETY MESSAGES:")
            for message in safety['messages']:
                summary.append(f"  • {message}")
            summary.append("")
        
        # Recommendations
        if risk['recommendations']:
            summary.append("RECOMMENDATIONS:")
            for rec in risk['recommendations']:
                summary.append(f"  • {rec}")
            summary.append("")
        
        summary.append("=" * 60)
        
        return "\n".join(summary)
    
    def check_rebalancing(self, current_allocation: Dict[str, float] = None) -> Dict:
        """
        Check if the current portfolio needs rebalancing based on drift analysis.
        
        This method compares the current portfolio allocation with the target allocation
        to determine if rebalancing is necessary. It uses the Caretaker component to
        analyze allocation drift and create a rebalancing plan if needed.
        
        Rebalancing is typically triggered when:
        - Asset weights drift beyond acceptable thresholds (usually 5-10%)
        - Market conditions change significantly
        - Risk metrics exceed target levels
        - Time-based rebalancing schedule is reached
        
        Args:
            current_allocation (Dict[str, float], optional): Current portfolio allocation
                If None, uses the target allocation from the current portfolio
                
        Returns:
            Dict: Rebalancing analysis containing:
                - action_needed: Boolean indicating if rebalancing is required
                - drift_analysis: Analysis of allocation drift
                - rebalance_plan: Detailed rebalancing strategy
                - cost_analysis: Estimated rebalancing costs
        """
        if not self.current_portfolio:
            return {"error": "No current portfolio"}
        
        if current_allocation is None:
            # Use target allocation as current (for demonstration)
            current_allocation = self.current_portfolio['allocation_plan']['allocation']
        
        target_allocation = self.current_portfolio['allocation_plan']['allocation']
        portfolio_value = self.current_portfolio['parameters']['budget']
        
        # Create rebalance plan
        rebalance_plan = self.caretaker.create_rebalance_plan(
            current_allocation, target_allocation, portfolio_value
        )
        
        return rebalance_plan
    
    def get_leaderboard(self, asset_class: str = None, top_n: int = 10) -> pd.DataFrame:
        """
        Get a ranked leaderboard of assets based on ML analysis scores.
        
        This method creates a leaderboard showing the top-performing assets based on
        the comprehensive ML analysis performed by the Research Crew. Assets are ranked
        by their composite score, which combines momentum, volatility, drawdown, and
        sentiment analysis.
        
        The leaderboard is useful for:
        - Understanding which assets scored highest in the analysis
        - Comparing performance across different asset classes
        - Identifying investment opportunities
        - Portfolio optimization and selection
        
        Args:
            asset_class (str, optional): Specific asset class to filter by
                - 'shares': Australian equities
                - 'bonds': Fixed income securities
                - 'commodities': Commodity investments
                - 'crypto': Cryptocurrencies
                - 'fx': Foreign exchange
                - None: Include all asset classes
            top_n (int): Number of top assets to include in the leaderboard
            
        Returns:
            pd.DataFrame: Leaderboard with columns:
                - ticker: Asset symbol
                - current_price: Latest price
                - composite_score: Overall ML score (0-1)
                - momentum_score: Momentum analysis score
                - volatility_score: Volatility analysis score
                - drawdown_score: Drawdown analysis score
                - sentiment_score: Sentiment analysis score
        """
        if not self.current_portfolio:
            return pd.DataFrame()
        
        analysis_results = self.current_portfolio['analysis_results']
        
        if asset_class:
            if asset_class in analysis_results:
                return self.research_crew.get_leaderboard(analysis_results[asset_class], top_n)
            else:
                return pd.DataFrame()
        else:
            # Combine all asset classes
            all_assets = []
            for class_name, assets in analysis_results.items():
                for asset in assets:
                    # Create a copy to avoid modifying original
                    asset_copy = asset.copy()
                    asset_copy['asset_class'] = class_name
                    all_assets.append(asset_copy)
            
            return self.research_crew.get_leaderboard(all_assets, top_n)
    
    def get_risk_dashboard(self) -> Dict:
        """
        Get a comprehensive risk dashboard with advanced risk metrics.
        
        This method provides a detailed risk analysis dashboard that includes
        portfolio volatility, risk attribution, Value at Risk (VaR), Conditional
        Value at Risk (CVaR), and other advanced risk metrics. The dashboard
        is designed for risk managers and sophisticated investors who need
        detailed risk analysis.
        
        The risk dashboard includes:
        - Portfolio volatility vs target volatility
        - Risk attribution by asset class
        - VaR and CVaR calculations
        - Risk score and budget compliance
        - Risk management recommendations
        
        Returns:
            Dict: Comprehensive risk dashboard containing:
                - portfolio_volatility: Current portfolio volatility
                - target_volatility: Target volatility from risk budget
                - risk_attribution: Risk contribution by asset class
                - var_metrics: VaR and CVaR calculations
                - risk_score: Overall risk score (0-1)
                - within_budget: Boolean indicating if within risk budget
                - recommendations: Risk management recommendations
        """
        if not self.current_portfolio:
            return {"error": "No current portfolio"}
        
        risk_report = self.current_portfolio['risk_report']
        allocation = self.current_portfolio['allocation_plan']['allocation']
        
        # Calculate additional risk metrics
        risk_attribution = self.risk_manager.calculate_risk_attribution(allocation)
        var_metrics = self.risk_manager.calculate_var_cvar(allocation)
        
        return {
            'portfolio_volatility': risk_report['portfolio_volatility'],
            'target_volatility': risk_report['target_volatility'],
            'risk_attribution': risk_attribution,
            'var_metrics': var_metrics,
            'risk_score': risk_report['risk_score'],
            'within_budget': risk_report['within_risk_budget'],
            'recommendations': risk_report['recommendations']
        }
    
    @log_function_performance(logger)
    def create_user_portfolio(self, user_id: str, portfolio_name: str, 
                            risk_level: RiskLevel, budget: float,
                            preferred_assets: Optional[List[str]] = None,
                            custom_settings: Optional[Dict[str, Any]] = None) -> Dict:
        """
        Create a user-customized portfolio with enhanced configuration management.
        
        Args:
            user_id: Unique user identifier
            portfolio_name: Name for the portfolio
            risk_level: Risk level preference (conservative, moderate, aggressive, custom)
            budget: Investment budget in dollars
            preferred_assets: List of preferred asset symbols
            custom_settings: Custom configuration overrides
            
        Returns:
            Complete portfolio with user-specific configuration
        """
        logger.info(f"Creating user portfolio: {portfolio_name} for user {user_id}")
        
        try:
            # Create or load user configuration
            config = self.config_manager.create_portfolio_config(
                user_id=user_id,
                portfolio_name=portfolio_name,
                risk_level=risk_level,
                preferred_assets=preferred_assets,
                custom_settings=custom_settings
            )
            
            # Validate configuration
            validation_results = self.validator.validate_user_config(config.__dict__)
            if not all(r.is_valid for r in validation_results if r.severity.value == 'error'):
                error_messages = [r.message for r in validation_results if not r.is_valid and r.severity.value == 'error']
                raise ValidationError(f"Configuration validation failed: {'; '.join(error_messages)}")
            
            # Store configuration
            self.config_manager.save_config(config)
            self.user_configs[f"{user_id}_{portfolio_name}"] = config
            
            # Create portfolio using configuration
            portfolio = self.create_portfolio(
                time_horizon="long_term",  # Default to long-term
                budget=budget,
                risk_budget=config.risk_config.target_volatility,
                risk_profile=risk_level.value
            )
            
            # Add user configuration to portfolio
            portfolio['user_config'] = config.__dict__
            portfolio['user_id'] = user_id
            portfolio['portfolio_name'] = portfolio_name
            
            # Log user action
            audit_logger.log_user_action(user_id, "create_portfolio", "portfolio_manager",
                                       portfolio_id=portfolio.get('portfolio_id'),
                                       risk_level=risk_level.value,
                                       budget=budget)
            
            return portfolio
            
        except Exception as e:
            logger.error(f"Failed to create user portfolio: {e}", exception=e)
            raise
    
    @log_function_performance(logger)
    def validate_portfolio_data(self, portfolio: Dict) -> Dict[str, Any]:
        """
        Comprehensive validation of portfolio data and calculations.
        
        Args:
            portfolio: Portfolio dictionary to validate
            
        Returns:
            Validation summary with detailed results
        """
        logger.info("Validating portfolio data and calculations")
        
        validation_results = []
        
        try:
            # Validate asset data
            if 'analysis_results' in portfolio:
                for asset_class, analysis in portfolio['analysis_results'].items():
                    if 'data' in analysis and analysis['data'] is not None:
                        data_results = self.validator.validate_asset_data(analysis['data'])
                        validation_results.extend(data_results)
            
            # Validate portfolio weights
            if 'selected_assets' in portfolio:
                weights = {asset: info['weight'] for asset, info in portfolio['selected_assets'].items()}
                weight_results = self.validator.validate_portfolio_weights(weights)
                validation_results.extend(weight_results)
            
            # Validate risk parameters
            if 'risk_report' in portfolio:
                risk_config = {
                    'target_volatility': portfolio['parameters'].get('risk_budget', 0.1),
                    'var_confidence_level': 0.95,
                    'max_drawdown_limit': 0.25
                }
                risk_results = self.validator.validate_risk_parameters(risk_config)
                validation_results.extend(risk_results)
            
            # Validate optimization results
            if 'allocation_plan' in portfolio:
                plan = portfolio['allocation_plan']
                if all(key in plan for key in ['expected_return', 'volatility', 'sharpe_ratio']):
                    weights = plan.get('weights', {})
                    opt_results = self.validator.validate_optimization_result(
                        weights, plan['expected_return'], plan['volatility'], plan['sharpe_ratio']
                    )
                    validation_results.extend(opt_results)
            
            # Generate validation summary
            summary = self.validator.get_validation_summary(validation_results)
            
            # Store validation results
            self.validation_results[portfolio.get('portfolio_id', 'unknown')] = {
                'results': validation_results,
                'summary': summary,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Portfolio validation completed: {summary['is_valid']}")
            return summary
            
        except Exception as e:
            logger.error("Portfolio validation failed", exception=e)
            return {'is_valid': False, 'error': str(e)}
    
    def get_available_assets(self, asset_class: Optional[str] = None) -> List[Dict]:
        """
        Get available assets based on user preferences and filters.
        
        Args:
            asset_class: Optional asset class filter
            
        Returns:
            List of available assets with metadata
        """
        logger.info(f"Getting available assets for class: {asset_class}")
        
        try:
            assets = self.config_manager.get_available_assets()
            
            if asset_class:
                assets = [a for a in assets if a.asset_class.value == asset_class]
            
            # Convert to dictionary format
            asset_list = []
            for asset in assets:
                asset_dict = {
                    'symbol': asset.symbol,
                    'name': asset.name,
                    'asset_class': asset.asset_class.value,
                    'exchange': asset.exchange,
                    'currency': asset.currency,
                    'enabled': asset.enabled,
                    'min_weight': asset.min_weight,
                    'max_weight': asset.max_weight
                }
                asset_list.append(asset_dict)
            
            return asset_list
            
        except Exception as e:
            logger.error("Failed to get available assets", exception=e)
            return []
    
    def add_custom_asset(self, symbol: str, name: str, asset_class: str,
                        exchange: str, currency: str = "USD",
                        volatility: Optional[float] = None) -> Dict:
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
            Asset configuration dictionary
        """
        logger.info(f"Adding custom asset: {symbol} ({name})")
        
        try:
            from .config.user_config import AssetClass
            asset_class_enum = AssetClass(asset_class)
            
            asset_config = self.config_manager.add_custom_asset(
                symbol=symbol,
                name=name,
                asset_class=asset_class_enum,
                exchange=exchange,
                currency=currency,
                volatility=volatility
            )
            
            # Log system action
            audit_logger.log_system_action("add_custom_asset", "portfolio_manager",
                                         symbol=symbol, name=name, asset_class=asset_class)
            
            return {
                'symbol': asset_config.symbol,
                'name': asset_config.name,
                'asset_class': asset_config.asset_class.value,
                'exchange': asset_config.exchange,
                'currency': asset_config.currency,
                'custom_volatility': asset_config.custom_volatility
            }
            
        except Exception as e:
            logger.error(f"Failed to add custom asset {symbol}", exception=e)
            raise
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get comprehensive system health status.
        
        Returns:
            System health report with component status and metrics
        """
        logger.info("Checking system health")
        
        health_report = {
            'overall_status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': self.component_status.copy(),
            'performance_metrics': self.performance_metrics.copy(),
            'validation_summary': {
                'total_validations': len(self.validation_results),
                'recent_failures': sum(1 for v in self.validation_results.values() 
                                     if not v['summary']['is_valid'])
            },
            'system_uptime': self._calculate_system_uptime(),
            'recommendations': []
        }
        
        # Check component health
        inactive_components = [comp for comp, status in self.component_status.items() 
                             if status != 'active']
        if inactive_components:
            health_report['overall_status'] = 'degraded'
            health_report['recommendations'].append(f"Inactive components: {inactive_components}")
        
        # Check validation failures
        recent_failures = health_report['validation_summary']['recent_failures']
        if recent_failures > 0:
            health_report['recommendations'].append(f"{recent_failures} recent validation failures")
        
        return health_report
    
    def _calculate_system_uptime(self) -> str:
        """Calculate system uptime."""
        # This would be implemented with actual uptime tracking
        return "24 hours"  # Placeholder
    
    def export_portfolio_report(self, portfolio: Dict, format: str = "json") -> str:
        """
        Export comprehensive portfolio report in specified format.
        
        Args:
            portfolio: Portfolio to export
            format: Export format (json, csv, html)
            
        Returns:
            Exported report content
        """
        logger.info(f"Exporting portfolio report in {format} format")
        
        try:
            if format.lower() == "json":
                import json
                return json.dumps(portfolio, indent=2, default=str)
            
            elif format.lower() == "csv":
                # Export key metrics as CSV
                import io
                output = io.StringIO()
                
                # Portfolio summary
                output.write("Metric,Value\n")
                output.write(f"Portfolio ID,{portfolio.get('portfolio_id', 'N/A')}\n")
                output.write(f"Budget,${portfolio.get('parameters', {}).get('budget', 0):,.2f}\n")
                output.write(f"Risk Budget,{portfolio.get('parameters', {}).get('risk_budget', 0):.1%}\n")
                
                # Asset allocation
                if 'selected_assets' in portfolio:
                    output.write("\nAsset,Weight,Amount\n")
                    for asset, info in portfolio['selected_assets'].items():
                        weight = info.get('weight', 0)
                        amount = portfolio.get('parameters', {}).get('budget', 0) * weight
                        output.write(f"{asset},{weight:.1%},${amount:,.2f}\n")
                
                return output.getvalue()
            
            elif format.lower() == "html":
                # Generate HTML report
                html_content = f"""
                <html>
                <head><title>Portfolio Report</title></head>
                <body>
                    <h1>AI Portfolio Management Report</h1>
                    <h2>Portfolio Summary</h2>
                    <p>Portfolio ID: {portfolio.get('portfolio_id', 'N/A')}</p>
                    <p>Budget: ${portfolio.get('parameters', {}).get('budget', 0):,.2f}</p>
                    <p>Risk Budget: {portfolio.get('parameters', {}).get('risk_budget', 0):.1%}</p>
                    
                    <h2>Asset Allocation</h2>
                    <table border="1">
                        <tr><th>Asset</th><th>Weight</th><th>Amount</th></tr>
                """
                
                if 'selected_assets' in portfolio:
                    for asset, info in portfolio['selected_assets'].items():
                        weight = info.get('weight', 0)
                        amount = portfolio.get('parameters', {}).get('budget', 0) * weight
                        html_content += f"<tr><td>{asset}</td><td>{weight:.1%}</td><td>${amount:,.2f}</td></tr>"
                
                html_content += """
                    </table>
                </body>
                </html>
                """
                
                return html_content
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Failed to export portfolio report: {e}", exception=e)
            raise

# Example usage and testing
if __name__ == "__main__":
    """
    Example usage of the Portfolio Manager system.
    
    This section demonstrates how to use the AI Portfolio Management System
    to create, analyze, and manage investment portfolios. The example shows
    the complete workflow from portfolio creation to risk analysis.
    
    This code can be run directly to test the system functionality and
    serves as a reference for integrating the system into other applications.
    """
    
    # Initialize the Portfolio Manager with all AI/ML components
    print("🤖 Initializing AI Portfolio Management System...")
    pm = PortfolioManager()
    
    # Create a sample portfolio using AI/ML optimization
    print("\n📊 Creating AI-optimized portfolio...")
    print("Parameters: Long-term horizon, $2,500 budget, 10% risk budget, moderate profile")
    
    portfolio = pm.create_portfolio(
        time_horizon="long_term",      # 5+ year investment horizon
        budget=2500,                  # $2,500 investment amount
        risk_budget=0.10,             # 10% target volatility
        sleep_better_dial=0.2,        # Slight risk reduction
        risk_profile="moderate"        # Balanced risk-return profile
    )
    
    # Display comprehensive portfolio summary
    print("\n📋 Portfolio Summary:")
    print("=" * 60)
    summary = pm.get_portfolio_summary(portfolio)
    print(summary)
    
    # Check if portfolio needs rebalancing
    print("\n🔄 Checking rebalancing requirements...")
    rebalance = pm.check_rebalancing()
    print(f"Rebalancing needed: {rebalance.get('action_needed', 'Unknown')}")
    
    # Get top-performing assets leaderboard
    print("\n🏆 Top Performing Assets (ML Analysis):")
    print("=" * 50)
    leaderboard = pm.get_leaderboard(top_n=5)
    if not leaderboard.empty:
        print(leaderboard.to_string(index=False))
    else:
        print("No leaderboard data available")
    
    # Get comprehensive risk dashboard
    print("\n⚠️ Risk Dashboard:")
    print("=" * 30)
    risk_dashboard = pm.get_risk_dashboard()
    
    if 'error' not in risk_dashboard:
        print(f"Portfolio Volatility: {risk_dashboard['portfolio_volatility']:.1%}")
        print(f"Target Volatility: {risk_dashboard['target_volatility']:.1%}")
        print(f"Risk Score: {risk_dashboard['risk_score']:.2f}")
        print(f"Within Risk Budget: {'Yes' if risk_dashboard['within_budget'] else 'No'}")
        
        if risk_dashboard.get('recommendations'):
            print("\nRisk Management Recommendations:")
            for rec in risk_dashboard['recommendations']:
                print(f"  • {rec}")
    else:
        print(f"Risk dashboard error: {risk_dashboard['error']}")
    
    print("\n✅ AI Portfolio Management System demonstration completed!")
    print("🎯 The system successfully created an AI-optimized portfolio with:")
    print("   - Machine learning-based asset analysis")
    print("   - Risk management and safety checks")
    print("   - Comprehensive buy list and trade orders")
    print("   - Advanced risk metrics and recommendations")

