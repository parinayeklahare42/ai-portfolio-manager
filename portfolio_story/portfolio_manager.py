"""
The Portfolio Story - Main Portfolio Manager
Orchestrates all components to create and manage portfolios
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta

from .data.librarian import Librarian
from .models.research_crew import ResearchCrew
from .models.planner import Planner
from .models.selector import Selector
from .safety.safety_officer import SafetyOfficer
from .safety.risk_manager import RiskManager
from .utils.shopkeeper import Shopkeeper
from .utils.caretaker import Caretaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PortfolioManager:
    """
    The main Portfolio Manager orchestrates all components:
    1. The Librarian - Data fetching
    2. The Research Crew - AI/ML analysis
    3. The Planner - Asset allocation
    4. The Selector - Asset selection
    5. The Safety Officer - Risk management
    6. The Risk Manager - Volatility targeting
    7. The Shopkeeper - Trade execution
    8. The Caretaker - Rebalancing
    """
    
    def __init__(self):
        # Initialize all components
        self.librarian = Librarian()
        self.research_crew = ResearchCrew()
        self.planner = Planner()
        self.selector = Selector()
        self.safety_officer = SafetyOfficer()
        self.risk_manager = RiskManager()
        self.shopkeeper = Shopkeeper()
        self.caretaker = Caretaker()
        
        # Portfolio state
        self.current_portfolio = None
        self.last_rebalance_date = None
    
    def create_portfolio(self, time_horizon: str, budget: float, 
                        risk_budget: float = 0.10, sleep_better_dial: float = 0.0,
                        risk_profile: str = "moderate") -> Dict:
        """
        Create a new portfolio based on user requirements
        
        Args:
            time_horizon: 'short_term', 'medium_term', or 'long_term'
            budget: Total investment amount
            risk_budget: Target volatility (e.g., 0.10 for 10%)
            sleep_better_dial: Risk adjustment (0-1, higher = more conservative)
            risk_profile: 'conservative', 'moderate', or 'aggressive'
            
        Returns:
            Complete portfolio with buy list and analysis
        """
        logger.info(f"Creating portfolio: {time_horizon}, ${budget:,.2f}, risk={risk_budget:.1%}")
        
        try:
            # Step 1: Fetch data (The Librarian)
            logger.info("Step 1: Fetching market data...")
            all_data = self.librarian.get_all_data()
            market_summary = self.librarian.get_market_summary()
            
            # Step 2: Analyze assets (The Research Crew)
            logger.info("Step 2: Analyzing assets...")
            analysis_results = {}
            for asset_class, data_dict in all_data.items():
                if data_dict:  # Only analyze if we have data
                    analysis_results[asset_class] = self.research_crew.analyze_asset_class(
                        asset_class, data_dict
                    )
            
            # Step 3: Create allocation plan (The Planner)
            logger.info("Step 3: Creating allocation plan...")
            allocation_plan = self.planner.create_portfolio_plan(
                time_horizon, risk_profile, sleep_better_dial, risk_budget
            )
            
            # Step 4: Select assets (The Selector)
            logger.info("Step 4: Selecting assets...")
            selected_assets = self.selector.create_portfolio_selection(
                analysis_results, allocation_plan['allocation']
            )
            
            # Step 5: Safety checks (The Safety Officer)
            logger.info("Step 5: Running safety checks...")
            safety_results = self.safety_officer.run_safety_checks(
                allocation_plan['allocation'],
                selected_assets,
                sleep_better_dial
            )
            
            # Step 6: Risk management (The Risk Manager)
            logger.info("Step 6: Managing risk...")
            risk_report = self.risk_manager.generate_risk_report(
                safety_results['final_allocation'], risk_budget
            )
            
            # Step 7: Create buy list (The Shopkeeper)
            logger.info("Step 7: Creating buy list...")
            dollar_amounts = self.shopkeeper.calculate_dollar_amounts(
                safety_results['final_allocation'], budget
            )
            trade_orders = self.shopkeeper.calculate_share_quantities(
                selected_assets, dollar_amounts
            )
            buy_list = self.shopkeeper.create_buy_list(trade_orders, budget)
            
            # Step 8: Create portfolio summary
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
            
            # Store current portfolio
            self.current_portfolio = portfolio
            
            logger.info("Portfolio creation completed successfully")
            return portfolio
            
        except Exception as e:
            logger.error(f"Portfolio creation failed: {e}")
            raise
    
    def get_portfolio_summary(self, portfolio: Dict) -> str:
        """
        Create human-readable portfolio summary
        
        Args:
            portfolio: Portfolio dictionary
            
        Returns:
            Formatted summary string
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
        Check if portfolio needs rebalancing
        
        Args:
            current_allocation: Current portfolio allocation
            
        Returns:
            Rebalancing analysis
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
        Get asset leaderboard
        
        Args:
            asset_class: Specific asset class or None for all
            top_n: Number of top assets to show
            
        Returns:
            Leaderboard DataFrame
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
        Get comprehensive risk dashboard
        
        Returns:
            Risk dashboard data
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

# Example usage and testing
if __name__ == "__main__":
    # Initialize the Portfolio Manager
    pm = PortfolioManager()
    
    # Create a sample portfolio
    print("Creating sample portfolio...")
    portfolio = pm.create_portfolio(
        time_horizon="long_term",
        budget=2500,
        risk_budget=0.10,
        sleep_better_dial=0.2,
        risk_profile="moderate"
    )
    
    # Display summary
    summary = pm.get_portfolio_summary(portfolio)
    print(summary)
    
    # Check rebalancing
    print("\nChecking rebalancing...")
    rebalance = pm.check_rebalancing()
    print(f"Rebalancing needed: {rebalance['action_needed']}")
    
    # Get leaderboard
    print("\nTop assets:")
    leaderboard = pm.get_leaderboard(top_n=5)
    print(leaderboard)
    
    # Get risk dashboard
    print("\nRisk dashboard:")
    risk_dashboard = pm.get_risk_dashboard()
    print(f"Portfolio volatility: {risk_dashboard['portfolio_volatility']:.1%}")
    print(f"Risk score: {risk_dashboard['risk_score']:.2f}")

