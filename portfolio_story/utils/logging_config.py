"""
Comprehensive Logging Configuration for AI Portfolio Management System

This module provides centralized logging configuration with different log levels,
formatters, and handlers for various components of the portfolio management system.

Key Features:
- Structured logging with different log levels
- Component-specific loggers
- File and console logging
- Performance monitoring and metrics logging
- Error tracking and debugging information
- Audit trail for portfolio decisions
"""

import logging
import logging.handlers
import sys
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import traceback
import functools

class PortfolioLogger:
    """
    Enhanced logger for portfolio management system with structured logging.
    
    This logger provides specialized logging capabilities for different components
    of the portfolio management system, including performance tracking, error
    monitoring, and audit trails.
    """
    
    def __init__(self, name: str, log_dir: str = "logs"):
        """
        Initialize portfolio logger.
        
        Args:
            name: Logger name (usually module name)
            log_dir: Directory for log files
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup logging handlers for different log levels."""
        # Console handler for INFO and above
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for all levels
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.name}.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"{self.name}_errors.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        self.logger.addHandler(error_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with additional context."""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with additional context."""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with additional context."""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message with optional exception details."""
        if exception:
            kwargs['exception_type'] = type(exception).__name__
            kwargs['exception_message'] = str(exception)
            kwargs['traceback'] = traceback.format_exc()
        
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log critical message with optional exception details."""
        if exception:
            kwargs['exception_type'] = type(exception).__name__
            kwargs['exception_message'] = str(exception)
            kwargs['traceback'] = traceback.format_exc()
        
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log message with additional context information."""
        if kwargs:
            context_str = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            full_message = f"{message} | Context: {context_str}"
        else:
            full_message = message
        
        self.logger.log(level, full_message)
    
    def log_performance(self, operation: str, duration: float, **metrics):
        """Log performance metrics for operations."""
        self.info(f"Performance: {operation} completed in {duration:.3f}s", 
                 op_name=operation, duration=duration, **metrics)
    
    def log_portfolio_action(self, action: str, portfolio_id: str, **details):
        """Log portfolio-related actions for audit trail."""
        self.info(f"Portfolio Action: {action}", 
                 action_type=action, portfolio_id=portfolio_id, **details)
    
    def log_optimization_result(self, method: str, objective_value: float, **details):
        """Log optimization results."""
        self.info(f"Optimization: {method} achieved objective {objective_value:.6f}", 
                 opt_method=method, objective_value=objective_value, **details)

def setup_portfolio_logging(log_dir: str = "logs", level: str = "INFO") -> Dict[str, PortfolioLogger]:
    """
    Setup comprehensive logging for the entire portfolio management system.
    
    Args:
        log_dir: Directory for log files
        level: Global logging level
        
        Returns:
            Dictionary of component loggers
    """
    # Set global logging level
    logging.basicConfig(level=getattr(logging, level.upper()))
    
    # Create component loggers
    loggers = {
        'portfolio_manager': PortfolioLogger('portfolio_manager', log_dir),
        'data_librarian': PortfolioLogger('data_librarian', log_dir),
        'research_crew': PortfolioLogger('research_crew', log_dir),
        'planner': PortfolioLogger('planner', log_dir),
        'risk_manager': PortfolioLogger('risk_manager', log_dir),
        'selector': PortfolioLogger('selector', log_dir),
        'safety_officer': PortfolioLogger('safety_officer', log_dir),
        'shopkeeper': PortfolioLogger('shopkeeper', log_dir),
        'caretaker': PortfolioLogger('caretaker', log_dir),
        'config': PortfolioLogger('config', log_dir),
        'dashboard': PortfolioLogger('dashboard', log_dir),
        'api': PortfolioLogger('api', log_dir)
    }
    
    # Log system startup
    main_logger = loggers['portfolio_manager']
    main_logger.info("Portfolio Management System Logging Initialized", 
                    log_dir=str(log_dir), log_level=level)
    
    return loggers

def log_function_performance(logger: PortfolioLogger):
    """Decorator to log function performance."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.log_performance(func.__name__, duration, 
                                     success=True, args_count=len(args), 
                                     kwargs_count=len(kwargs))
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Function {func.__name__} failed", exception=e,
                           duration=duration, args_count=len(args), 
                           kwargs_count=len(kwargs))
                raise
        return wrapper
    return decorator

def log_portfolio_decision(logger: PortfolioLogger):
    """Decorator to log portfolio decisions."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                # Extract portfolio information from result if possible
                if isinstance(result, dict) and 'portfolio_id' in result:
                    logger.log_portfolio_action(func.__name__, result['portfolio_id'],
                                              decision_type=func.__name__, 
                                              success=True)
                else:
                    logger.log_portfolio_action(func.__name__, "unknown",
                                              decision_type=func.__name__, 
                                              success=True)
                return result
            except Exception as e:
                logger.error(f"Portfolio decision {func.__name__} failed", exception=e)
                raise
        return wrapper
    return decorator

class AuditLogger:
    """
    Specialized logger for audit trails and compliance tracking.
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create audit logger
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            # Audit file handler
            audit_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / "audit.log",
                maxBytes=20*1024*1024,  # 20MB
                backupCount=10
            )
            audit_handler.setLevel(logging.INFO)
            
            # JSON formatter for structured audit logs
            class JSONFormatter(logging.Formatter):
                def format(self, record):
                    log_entry = {
                        'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                        'level': record.levelname,
                        'component': getattr(record, 'component', 'unknown'),
                        'action': getattr(record, 'action', 'unknown'),
                        'user_id': getattr(record, 'user_id', 'system'),
                        'portfolio_id': getattr(record, 'portfolio_id', None),
                        'message': record.getMessage(),
                        'details': getattr(record, 'details', {})
                    }
                    return json.dumps(log_entry, default=str)
            
            audit_handler.setFormatter(JSONFormatter())
            self.logger.addHandler(audit_handler)
    
    def log_user_action(self, user_id: str, action: str, component: str, 
                       portfolio_id: Optional[str] = None, **details):
        """Log user actions for audit trail."""
        self.logger.info(f"User action: {action}", 
                        extra={
                            'component': component,
                            'action': action,
                            'user_id': user_id,
                            'portfolio_id': portfolio_id,
                            'details': details
                        })
    
    def log_system_action(self, action: str, component: str, **details):
        """Log system actions for audit trail."""
        self.logger.info(f"System action: {action}", 
                        extra={
                            'component': component,
                            'action': action,
                            'user_id': 'system',
                            'details': details
                        })
    
    def log_portfolio_change(self, portfolio_id: str, change_type: str, 
                           old_values: Dict, new_values: Dict, user_id: str):
        """Log portfolio changes for audit trail."""
        self.logger.info(f"Portfolio change: {change_type}", 
                        extra={
                            'component': 'portfolio_manager',
                            'action': 'portfolio_change',
                            'portfolio_id': portfolio_id,
                            'user_id': user_id,
                            'details': {
                                'change_type': change_type,
                                'old_values': old_values,
                                'new_values': new_values,
                                'timestamp': datetime.now().isoformat()
                            }
                        })

class PerformanceLogger:
    """
    Specialized logger for performance monitoring and metrics.
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create performance logger
        self.logger = logging.getLogger('performance')
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            # Performance file handler
            perf_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / "performance.log",
                maxBytes=50*1024*1024,  # 50MB
                backupCount=5
            )
            perf_handler.setLevel(logging.INFO)
            
            # CSV-like formatter for performance metrics
            class PerformanceFormatter(logging.Formatter):
                def format(self, record):
                    return (f"{datetime.fromtimestamp(record.created).isoformat()},"
                           f"{record.levelname},"
                           f"{getattr(record, 'operation', 'unknown')},"
                           f"{getattr(record, 'duration', 0):.6f},"
                           f"{getattr(record, 'memory_usage', 0):.2f},"
                           f"{getattr(record, 'cpu_usage', 0):.2f},"
                           f"{getattr(record, 'success', 'unknown')},"
                           f"{record.getMessage()}")
            
            perf_handler.setFormatter(PerformanceFormatter())
            self.logger.addHandler(perf_handler)
    
    def log_operation(self, operation: str, duration: float, success: bool = True,
                     memory_usage: float = 0.0, cpu_usage: float = 0.0, **metrics):
        """Log operation performance metrics."""
        self.logger.info(f"Performance metric: {operation}", 
                        extra={
                            'operation': operation,
                            'duration': duration,
                            'memory_usage': memory_usage,
                            'cpu_usage': cpu_usage,
                            'success': success,
                            'metrics': metrics
                        })
    
    def log_data_processing(self, data_size: int, processing_time: float, 
                          records_processed: int, success: bool = True):
        """Log data processing performance."""
        throughput = records_processed / processing_time if processing_time > 0 else 0
        self.log_operation("data_processing", processing_time, success,
                          records_processed=records_processed,
                          data_size_mb=data_size / (1024 * 1024),
                          throughput_records_per_sec=throughput)
    
    def log_optimization_performance(self, method: str, duration: float, 
                                   iterations: int, convergence: bool, **metrics):
        """Log optimization performance."""
        self.log_operation(f"optimization_{method}", duration, convergence,
                          iterations=iterations, **metrics)

# Global loggers instance
_loggers = None
_audit_logger = None
_performance_logger = None

def get_logger(component: str) -> PortfolioLogger:
    """Get logger for specific component."""
    global _loggers
    if _loggers is None:
        _loggers = setup_portfolio_logging()
    
    return _loggers.get(component, _loggers['portfolio_manager'])

def get_audit_logger() -> AuditLogger:
    """Get audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger

def get_performance_logger() -> PerformanceLogger:
    """Get performance logger instance."""
    global _performance_logger
    if _performance_logger is None:
        _performance_logger = PerformanceLogger()
    return _performance_logger

# Example usage and testing
if __name__ == "__main__":
    print("=== AI Portfolio Logging System Demo ===\n")
    
    # Setup logging
    loggers = setup_portfolio_logging(level="DEBUG")
    audit_logger = get_audit_logger()
    perf_logger = get_performance_logger()
    
    # Test different loggers
    portfolio_logger = loggers['portfolio_manager']
    
    print("1. TESTING BASIC LOGGING")
    print("-" * 40)
    portfolio_logger.debug("Debug message for development")
    portfolio_logger.info("Portfolio system initialized successfully")
    portfolio_logger.warning("Market data connection slow")
    
    # Test error logging
    try:
        raise ValueError("Simulated error for testing")
    except Exception as e:
        portfolio_logger.error("An error occurred during portfolio optimization", exception=e)
    
    print("\n2. TESTING PERFORMANCE LOGGING")
    print("-" * 40)
    
    @log_function_performance(portfolio_logger)
    def sample_optimization():
        time.sleep(0.1)  # Simulate work
        return {"optimal_weights": {"SPY": 0.6, "BND": 0.4}}
    
    result = sample_optimization()
    print(f"Optimization result: {result}")
    
    print("\n3. TESTING AUDIT LOGGING")
    print("-" * 40)
    audit_logger.log_user_action("user123", "create_portfolio", "portfolio_manager",
                                portfolio_id="port_001", risk_level="moderate")
    audit_logger.log_system_action("rebalance_portfolio", "caretaker", 
                                  portfolio_id="port_001", drift_detected=0.05)
    
    print("\n4. TESTING PERFORMANCE METRICS")
    print("-" * 40)
    perf_logger.log_data_processing(1024*1024, 2.5, 1000)  # 1MB, 2.5s, 1000 records
    perf_logger.log_optimization_performance("markowitz", 1.2, 15, True, 
                                           objective_value=0.85, convergence_tolerance=1e-6)
    
    print("\n=== Logging System Demo Complete ===")
    print("Check the 'logs' directory for generated log files!")
