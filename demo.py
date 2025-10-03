#!/usr/bin/env python3
"""
The Portfolio Story - Enhanced Demo Script
Demonstrates the complete AI-powered portfolio management system with enhanced features
"""

import sys
import os
from datetime import datetime

# Add portfolio_story to path
sys.path.append('.')

try:
    from portfolio_story.portfolio_manager import PortfolioManager
    from portfolio_story.config.user_config import RiskLevel, UserConfigManager
    from portfolio_story.utils.logging_config import setup_portfolio_logging
    print("Enhanced Portfolio Story system imported successfully!")
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)

def main():
    """Main demonstration function with enhanced features"""
    print("=" * 60)
    print("THE PORTFOLIO STORY - ENHANCED AI-POWERED INVESTMENT MANAGEMENT")
    print("=" * 60)
    print(f"Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Setup enhanced logging
        print("Setting up enhanced logging system...")
        loggers = setup_portfolio_logging(level="INFO")
        print("Enhanced logging initialized successfully!")
        
        # Initialize the Enhanced Portfolio Manager
        print("Initializing Enhanced Portfolio Manager...")
        pm = PortfolioManager(config_dir="demo_config", log_dir="demo_logs")
        print("Enhanced Portfolio Manager initialized successfully!")
        print()
        
        # Demonstrate enhanced features
        print("ENHANCED FEATURES DEMO")
        print("-" * 40)
        
        # 1. User Configuration Management
        print("1. User Configuration Management")
        config_manager = UserConfigManager("demo_config")
        available_assets = pm.get_available_assets(asset_class="equities")
        print(f"   ✅ Available equity assets: {len(available_assets)}")
        
        # 2. System Health Monitoring
        print("2. System Health Monitoring")
        health_report = pm.get_system_health()
        print(f"   ✅ System Status: {health_report['overall_status'].upper()}")
        print(f"   ✅ Active Components: {len([c for c, s in health_report['components'].items() if s == 'active'])}")
        print()
        
        # Demo scenario: "Long term, $2,500" with NEW Professional Allocation Logic
        print("Creating portfolio: 'Long term, $2,500'")
        print("   - Time Horizon: Long term")
        print("   - Budget: $2,500")
        print("   - Risk Budget: 10% volatility")
        print("   - Risk Level: 3 (Moderate)")
        print("   - NEW: Professional-grade allocation with volatility capping!")
        print()
        
        # Show new risk-based allocation examples
        print("NEW REALISTIC ALLOCATION LOGIC")
        print("-" * 40)
        print("   Risk Level 1 (Very Conservative): 55% Bonds, 20% Equity, 15% Cash")
        print("   Risk Level 2 (Conservative): 45% Bonds, 30% Equity, 10% Cash") 
        print("   Risk Level 3 (Moderate): 35% Bonds, 40% Equity, 7% Cash")
        print("   Risk Level 4 (Aggressive): 25% Bonds, 55% Equity, 4% Cash")
        print("   Risk Level 5 (Very Aggressive): 21% Bonds, 61% Equity, 2% Cash")
        print("   ✅ NEW: Professional-grade allocation with volatility capping!")
        print("   ✅ NEW: Realistic financial logic with proper risk-return profiles!")
        print()
        
        # Create the portfolio using new allocation system
        portfolio = pm.create_portfolio(
            time_horizon="long_term",
            budget=2500,
            risk_budget=0.10,
            sleep_better_dial=3,  # Risk level 3 (Moderate)
            risk_profile="new_allocation_system"
        )
        
        print("Portfolio created successfully!")
        print(f"   Portfolio ID: {portfolio['portfolio_id']}")
        print()
        
        # Display portfolio summary
        print("PORTFOLIO SUMMARY")
        print("-" * 40)
        summary = pm.get_portfolio_summary(portfolio)
        print(summary)
        print()
        
        # Display buy list
        print("BUY LIST")
        print("-" * 40)
        buy_list = portfolio['buy_list']
        print(f"Total Budget: ${buy_list['summary']['total_budget']:,.2f}")
        print(f"Total Spent: ${buy_list['summary']['total_spent']:,.2f}")
        print(f"Leftover Cash: ${buy_list['summary']['total_leftover']:,.2f}")
        print(f"Number of Assets: {buy_list['summary']['num_assets']}")
        print()
        
        print("Trade Orders:")
        for order in buy_list['trade_orders']:
            print(f"  {order['ticker']}: {order['shares']} shares @ ${order['current_price']:.2f} = ${order['actual_cost']:.2f}")
        print()
        
        # Display risk metrics
        print("RISK METRICS")
        print("-" * 40)
        risk_dashboard = pm.get_risk_dashboard()
        print(f"Portfolio Volatility: {risk_dashboard['portfolio_volatility']:.1%}")
        print(f"Target Volatility: {risk_dashboard['target_volatility']:.1%}")
        print(f"Risk Score: {risk_dashboard['risk_score']:.2f}")
        print(f"Within Budget: {risk_dashboard['within_budget']}")
        print()
        
        # Display top assets
        print("TOP ASSETS")
        print("-" * 40)
        try:
            leaderboard = pm.get_leaderboard(top_n=5)
            if not leaderboard.empty and 'ticker' in leaderboard.columns:
                print("Top 5 Assets:")
                for i, (_, asset) in enumerate(leaderboard.head(5).iterrows(), 1):
                    asset_class = asset.get('asset_class', 'Unknown')
                    score = asset.get('composite_score', 0)
                    print(f"  {i}. {asset['ticker']} ({asset_class}): Score {score:.3f}")
            else:
                print("No leaderboard data available")
        except Exception as e:
            print(f"Leaderboard error: {e}")
        print()
        
        # Check rebalancing
        print("REBALANCING CHECK")
        print("-" * 40)
        rebalance = pm.check_rebalancing()
        print(f"Action Needed: {rebalance['action_needed']}")
        print(f"Total Turnover: {rebalance['turnover_percentage']:.1%}")
        print(f"Number of Trades: {rebalance['num_trades']}")
        print()
        
        # Display safety messages
        safety_results = portfolio['safety_results']
        if safety_results['messages']:
            print("SAFETY MESSAGES")
            print("-" * 40)
            for message in safety_results['messages']:
                print(f"  - {message}")
            print()
        
        # Display recommendations
        if risk_dashboard['recommendations']:
            print("RECOMMENDATIONS")
            print("-" * 40)
            for rec in risk_dashboard['recommendations']:
                print(f"  - {rec}")
            print()
        
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("The Portfolio Story demonstrates:")
        print("- AI/ML-powered asset selection")
        print("- Risk management and safety systems")
        print("- Transparent, explainable decisions")
        print("- Real-time market data integration")
        print("- Comprehensive portfolio analysis")
        print("=" * 60)
        
    except Exception as e:
        print(f"Demo failed: {e}")
        print("Please check the error and try again.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\nReady for presentation!")
        print("Run 'jupyter notebook portfolio_story_demo.ipynb' for interactive analysis")
    else:
        print("\nDemo failed. Please check the setup.")
        sys.exit(1)
