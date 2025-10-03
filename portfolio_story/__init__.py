"""
The Portfolio Story - Enhanced AI-Powered Investment Management
Main package initialization with comprehensive validation, logging, and configuration management
"""

# Core components
from .data.librarian import Librarian
from .models.research_crew import ResearchCrew
from .models.planner import Planner
from .models.selector import Selector
from .safety.safety_officer import SafetyOfficer
from .safety.risk_manager import RiskManager
from .utils.shopkeeper import Shopkeeper
from .utils.caretaker import Caretaker

# Enhanced systems
from .config.user_config import UserConfigManager, PortfolioConfig, RiskLevel, AssetClass
from .utils.logging_config import get_logger, get_audit_logger, get_performance_logger
from .utils.validation import PortfolioValidator, ValidationError

# Main portfolio manager
from .portfolio_manager import PortfolioManager

__version__ = "2.0.0"
__author__ = "Enhanced Portfolio Story Team"
__description__ = "Production-ready AI-powered investment portfolio management system"

__all__ = [
    # Core components
    'Librarian',
    'ResearchCrew', 
    'Planner',
    'Selector',
    'SafetyOfficer',
    'RiskManager',
    'Shopkeeper',
    'Caretaker',
    
    # Enhanced systems
    'UserConfigManager',
    'PortfolioConfig',
    'RiskLevel',
    'AssetClass',
    'get_logger',
    'get_audit_logger',
    'get_performance_logger',
    'PortfolioValidator',
    'ValidationError',
    
    # Main system
    'PortfolioManager'
]

