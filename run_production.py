#!/usr/bin/env python3
"""
Production Dashboard Launcher
Optimized for cloud deployment with proper configuration
"""

import os
import sys
import logging
from portfolio_story.ui.dashboard import app

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Get configuration from environment variables
    port = int(os.environ.get("PORT", 8050))
    host = os.environ.get("HOST", "0.0.0.0")
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    
    logger.info("🚀 Starting AI Portfolio Manager Dashboard...")
    logger.info(f"📊 Dashboard will be available at: http://{host}:{port}")
    logger.info(f"⚡ Production mode: {not debug}")
    logger.info("🌐 Optimized for cloud deployment")
    
    try:
        # Run with production settings
        app.run(
            debug=debug,
            host=host,
            port=port,
            dev_tools_hot_reload=False,
            dev_tools_ui=False,
            threaded=True
        )
    except Exception as e:
        logger.error(f"❌ Error starting dashboard: {e}")
        sys.exit(1)
