"""
Test suite for The Portfolio Story system
Tests all major components and functionality
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append('..')
sys.path.append('../..')

from portfolio_story.data.librarian import Librarian
from portfolio_story.models.research_crew import ResearchCrew
from portfolio_story.models.planner import Planner
from portfolio_story.models.selector import Selector
from portfolio_story.safety.safety_officer import SafetyOfficer
from portfolio_story.safety.risk_manager import RiskManager
from portfolio_story.utils.shopkeeper import Shopkeeper
from portfolio_story.utils.caretaker import Caretaker

class TestPortfolioSystem(unittest.TestCase):
    """Test suite for the complete portfolio system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.librarian = Librarian()
        self.research_crew = ResearchCrew()
        self.planner = Planner()
        self.selector = Selector()
        self.safety_officer = SafetyOfficer()
        self.risk_manager = RiskManager()
        self.shopkeeper = Shopkeeper()
        self.caretaker = Caretaker()
        
        # Create sample data for testing
        self.sample_data = self._create_sample_data()
        self.sample_allocation = {
            'shares': 0.55,
            'bonds': 0.25,
            'commodities': 0.10,
            'cash': 0.10
        }
    
    def _create_sample_data(self):
        """Create sample price data for testing"""
        dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
        sample_data = {}
        
        # Create sample data for different asset classes
        tickers = ['CBA.AX', 'BHP.AX', 'VGB.AX', 'GOLD.AX']
        for ticker in tickers:
            # Generate realistic price data
            np.random.seed(hash(ticker) % 2**32)  # Consistent random data
            returns = np.random.normal(0.0005, 0.02, len(dates))  # Daily returns
            prices = 100 * np.exp(np.cumsum(returns))  # Price series
            
            sample_data[ticker] = pd.DataFrame({
                'Close': prices,
                'Volume': np.random.randint(1000, 10000, len(dates))
            }, index=dates)
        
        return sample_data
    
    def test_librarian_initialization(self):
        """Test Librarian initialization"""
        self.assertIsInstance(self.librarian, Librarian)
        self.assertIsNotNone(self.librarian.asset_universe)
        self.assertIn('shares', self.librarian.asset_universe)
        self.assertIn('bonds', self.librarian.asset_universe)
    
    def test_research_crew_analysis(self):
        """Test Research Crew analysis functions"""
        # Test momentum calculation
        sample_data = self.sample_data['CBA.AX']
        momentum = self.research_crew.calculate_momentum_score(sample_data)
        self.assertIsInstance(momentum, float)
        self.assertGreaterEqual(momentum, 0)
        self.assertLessEqual(momentum, 1)
        
        # Test volatility calculation
        volatility = self.research_crew.calculate_volatility_score(sample_data)
        self.assertIsInstance(volatility, float)
        self.assertGreaterEqual(volatility, 0)
        self.assertLessEqual(volatility, 1)
        
        # Test drawdown calculation
        drawdown = self.research_crew.calculate_drawdown_score(sample_data)
        self.assertIsInstance(drawdown, float)
        self.assertGreaterEqual(drawdown, 0)
        self.assertLessEqual(drawdown, 1)
        
        # Test sentiment analysis
        sample_news = [
            {'title': 'Company reports strong quarterly earnings'},
            {'title': 'Stock price surges on positive outlook'}
        ]
        sentiment = self.research_crew.calculate_sentiment_score(sample_news)
        self.assertIsInstance(sentiment, float)
        self.assertGreaterEqual(sentiment, 0)
        self.assertLessEqual(sentiment, 1)
    
    def test_planner_allocation(self):
        """Test Planner allocation functions with new professional 5-level risk system"""
        # Test Level 1 (Very Conservative) - should have high bond allocation
        level1_allocation = self.planner.create_base_allocation(1, 'medium')
        self.assertIsInstance(level1_allocation, dict)
        self.assertAlmostEqual(sum(level1_allocation.values()), 1.0, places=2)
        self.assertGreater(level1_allocation.get('bonds', 0), 0.5)  # Should have >50% bonds
        self.assertLess(level1_allocation.get('shares', 0), 0.3)   # Should have <30% shares
        
        # Test Level 3 (Moderate) - should be balanced
        level3_allocation = self.planner.create_base_allocation(3, 'medium')
        self.assertIsInstance(level3_allocation, dict)
        self.assertAlmostEqual(sum(level3_allocation.values()), 1.0, places=2)
        # Moderate should have balanced allocation
        self.assertGreater(level3_allocation.get('shares', 0), 0.3)  # Should have >30% shares
        self.assertLess(level3_allocation.get('bonds', 0), 0.5)      # Should have <50% bonds
        
        # Test Level 5 (Very Aggressive) - should have high equity allocation
        level5_allocation = self.planner.create_base_allocation(5, 'medium')
        self.assertIsInstance(level5_allocation, dict)
        self.assertAlmostEqual(sum(level5_allocation.values()), 1.0, places=2)
        self.assertGreater(level5_allocation.get('shares', 0), level5_allocation.get('bonds', 0))
        self.assertGreater(level5_allocation.get('shares', 0), 0.5)  # Should have >50% shares
        
        # Test optimal allocation with volatility capping
        optimal_result = self.planner.create_optimal_allocation(25000, 'medium', 5, 15.0)
        self.assertIsInstance(optimal_result, dict)
        self.assertIn('weights', optimal_result)
        self.assertIn('predicted_vol_pct', optimal_result)
        self.assertIn('risk_status', optimal_result)
        self.assertAlmostEqual(sum(optimal_result['weights'].values()), 1.0, places=2)
        
        # Test sleep-better dial (legacy support)
        adjusted = self.planner.apply_sleep_better_dial(level3_allocation, 0.5)
        self.assertIsInstance(adjusted, dict)
        self.assertAlmostEqual(sum(adjusted.values()), 1.0, places=2)
        
        # Test risk budget (legacy support)
        risk_adjusted = self.planner.apply_risk_budget(level3_allocation, 0.10)
        self.assertIsInstance(risk_adjusted, dict)
        self.assertAlmostEqual(sum(risk_adjusted.values()), 1.0, places=2)
    
    def test_selector_asset_selection(self):
        """Test Selector asset selection"""
        # Create sample analysis results
        analysis_results = {
            'shares': [
                {'ticker': 'CBA.AX', 'composite_score': 0.85, 'current_price': 95.50},
                {'ticker': 'BHP.AX', 'composite_score': 0.78, 'current_price': 45.20}
            ],
            'bonds': [
                {'ticker': 'VGB.AX', 'composite_score': 0.75, 'current_price': 105.20}
            ]
        }
        
        # Test asset selection
        selected = self.selector.create_portfolio_selection(analysis_results, self.sample_allocation)
        self.assertIsInstance(selected, dict)
        self.assertIn('shares', selected)
        self.assertIn('bonds', selected)
    
    def test_safety_officer_checks(self):
        """Test Safety Officer safety checks"""
        # Test sleep-better dial
        result = self.safety_officer.check_sleep_better_dial(self.sample_allocation, 0.5)
        self.assertIsInstance(result, dict)
        self.assertIn('allocation', result)
        self.assertIn('adjustment', result)
        self.assertIn('message', result)
        
        # Test FX hedge
        fx_data = {'AUDUSD=X': 0.95, 'AUDEUR=X': 0.88}
        fx_result = self.safety_officer.check_fx_auto_hedge(fx_data)
        self.assertIsInstance(fx_result, dict)
        self.assertIn('recommendation', fx_result)
        self.assertIn('message', fx_result)
    
    def test_risk_manager_calculations(self):
        """Test Risk Manager calculations"""
        # Test portfolio volatility
        vol = self.risk_manager.calculate_portfolio_volatility(self.sample_allocation)
        self.assertIsInstance(vol, float)
        self.assertGreaterEqual(vol, 0)
        
        # Test risk attribution
        attribution = self.risk_manager.calculate_risk_attribution(self.sample_allocation)
        self.assertIsInstance(attribution, dict)
        self.assertAlmostEqual(sum(attribution.values()), 1.0, places=2)
        
        # Test VaR calculation
        var_metrics = self.risk_manager.calculate_var_cvar(self.sample_allocation)
        self.assertIsInstance(var_metrics, dict)
        self.assertIn('var_1y', var_metrics)
        self.assertIn('cvar_1y', var_metrics)
    
    def test_shopkeeper_execution(self):
        """Test Shopkeeper execution functions"""
        # Test dollar amount calculation
        dollar_amounts = self.shopkeeper.calculate_dollar_amounts(self.sample_allocation, 2500)
        self.assertIsInstance(dollar_amounts, dict)
        self.assertAlmostEqual(sum(dollar_amounts.values()), 2500, places=2)
        
        # Test share quantity calculation
        sample_assets = {
            'shares': [
                {'ticker': 'CBA.AX', 'current_price': 95.50, 'weight': 0.6, 'allocation_percentage': 0.33}
            ]
        }
        trades = self.shopkeeper.calculate_share_quantities(sample_assets, dollar_amounts)
        self.assertIsInstance(trades, list)
        if trades:
            self.assertIn('ticker', trades[0])
            self.assertIn('shares', trades[0])
            self.assertIn('actual_cost', trades[0])
    
    def test_caretaker_rebalancing(self):
        """Test Caretaker rebalancing functions"""
        # Test drift calculation
        current = {'shares': 0.60, 'bonds': 0.20, 'commodities': 0.10, 'cash': 0.10}
        target = {'shares': 0.55, 'bonds': 0.25, 'commodities': 0.10, 'cash': 0.10}
        drift = self.caretaker.calculate_portfolio_drift(current, target)
        self.assertIsInstance(drift, dict)
        self.assertIn('shares', drift)
        self.assertIn('bonds', drift)
        
        # Test rebalance plan
        plan = self.caretaker.create_rebalance_plan(current, target, 2500)
        self.assertIsInstance(plan, dict)
        self.assertIn('drift', plan)
        self.assertIn('trades', plan)
        self.assertIn('action_needed', plan)
    
    def test_integration_workflow(self):
        """Test complete integration workflow"""
        # This test simulates the complete workflow
        # Step 1: Create allocation plan
        allocation_plan = self.planner.create_portfolio_plan(
            'long', 3, 0.2, 0.10
        )
        self.assertIsInstance(allocation_plan, dict)
        self.assertIn('allocation', allocation_plan)
        
        # Step 2: Analyze sample data
        analysis_results = {}
        for ticker, data in self.sample_data.items():
            analysis = self.research_crew.analyze_asset(ticker, data, [])
            analysis_results[ticker] = analysis
        
        self.assertIsInstance(analysis_results, dict)
        self.assertGreater(len(analysis_results), 0)
        
        # Step 3: Create buy list
        dollar_amounts = self.shopkeeper.calculate_dollar_amounts(
            allocation_plan['allocation'], 2500
        )
        self.assertIsInstance(dollar_amounts, dict)
        self.assertAlmostEqual(sum(dollar_amounts.values()), 2500, places=2)
    
    def test_error_handling(self):
        """Test error handling and edge cases"""
        # Test with empty data
        empty_data = pd.DataFrame()
        momentum = self.research_crew.calculate_momentum_score(empty_data)
        self.assertEqual(momentum, 0.5)  # Should return neutral score
        
        # Test with invalid allocation
        invalid_allocation = {'shares': 0.5, 'bonds': 0.3}  # Sums to 0.8
        normalized = self.planner._normalize_allocation(invalid_allocation)
        self.assertAlmostEqual(sum(normalized.values()), 1.0, places=2)
        
        # Test with zero budget
        dollar_amounts = self.shopkeeper.calculate_dollar_amounts(
            self.sample_allocation, 0
        )
        self.assertIsInstance(dollar_amounts, dict)
        self.assertEqual(sum(dollar_amounts.values()), 0)
    
    def test_performance_metrics(self):
        """Test performance and efficiency metrics"""
        # Test that calculations complete in reasonable time
        import time
        
        start_time = time.time()
        vol = self.risk_manager.calculate_portfolio_volatility(self.sample_allocation)
        end_time = time.time()
        
        self.assertLess(end_time - start_time, 1.0)  # Should complete in under 1 second
        self.assertIsInstance(vol, float)
    
    def test_data_consistency(self):
        """Test data consistency across components"""
        # Test that allocation percentages are consistent
        allocation = self.planner.create_base_allocation(3, 'long')
        self.assertAlmostEqual(sum(allocation.values()), 1.0, places=2)
        
        # Test that risk calculations are consistent
        vol1 = self.risk_manager.calculate_portfolio_volatility(allocation)
        vol2 = self.risk_manager.calculate_portfolio_volatility(allocation)
        self.assertEqual(vol1, vol2)  # Should be deterministic

def run_tests():
    """Run all tests"""
    print("Running Portfolio Story Test Suite...")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPortfolioSystem)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nTest Suite {'PASSED' if success else 'FAILED'}")
    
    return success

if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
