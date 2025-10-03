#!/usr/bin/env python3
"""
Simple Dashboard Launcher
Run the AI Portfolio Manager Dashboard
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from portfolio_story.ui.dashboard import app
    
    if __name__ == "__main__":
        print("Starting AI Portfolio Manager Dashboard...")
        print("Dashboard will be available at: http://localhost:8050")
        print("Press Ctrl+C to stop the dashboard")
        print("-" * 50)
        
    # Run the dashboard with performance optimizations
    app.run(
        debug=False,  # Disable debug mode for better performance
        host='0.0.0.0',
        port=8050,
        dev_tools_hot_reload=False,  # Disable hot reload to prevent auto-refresh
        dev_tools_ui=False,  # Disable dev tools UI
        threaded=True  # Enable threading for better performance
    )
        
except ImportError as e:
    print(f"Error importing dashboard: {e}")
    print("Make sure you're in the correct directory and all dependencies are installed")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error starting dashboard: {e}")
    sys.exit(1)
