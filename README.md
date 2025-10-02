# 🚀 AI Portfolio Manager - Professional Dashboard

**Advanced AI-powered investment portfolio management system with interactive Dash dashboard.**

## 🌟 **Project Overview**

This is a comprehensive AI-powered portfolio management system that combines modern portfolio theory with advanced machine learning techniques to create optimal investment strategies for both novice and experienced investors.

### **🎯 Key Features**

- **🤖 AI-Powered Analysis**: Machine learning models for risk assessment, price prediction, and sentiment analysis
- **📊 Interactive Dashboard**: Professional Dash-based web interface with real-time visualizations
- **⚖️ Portfolio Optimization**: Modern portfolio theory with AI enhancements
- **🛡️ Risk Management**: Advanced risk metrics including VaR, Expected Shortfall, and drawdown analysis
- **📈 Real-time Data**: Live market data integration with intelligent caching
- **🎨 User-Friendly Interface**: Designed for both beginners and professionals

## 🏗️ **Project Structure**

```
finance-project/
├── portfolio_story/           # Core portfolio management system
│   ├── data/                 # Data fetching and caching
│   ├── models/               # AI/ML models and analysis
│   ├── safety/               # Risk management components
│   ├── utils/                # Utility functions
│   ├── ui/                   # Dashboard interface
│   └── tests/                # Test suite
├── data/                     # Market data cache
├── demo.py                   # Demo script
├── launcher.py               # System launcher
├── portfolio_story_demo.ipynb # Jupyter notebook demo
├── requirements.txt          # Dependencies
└── README.md                # This file
```

## 🚀 **Quick Start**

### **1. Installation**
```bash
# Clone the repository
git clone <repository-url>
cd finance-project

# Install dependencies
pip install -r requirements.txt
```

### **2. Run the Dashboard**

**Option A: Direct Dashboard**
```bash
python run_dashboard.py
```

**Option B: Windows Batch File**
```bash
start_dashboard.bat
```

**Option C: Interactive Launcher**
```bash
python launcher.py
```

### **3. Access the Dashboard**
- Open your browser and go to: `http://localhost:8050`
- The dashboard will load with a professional interface

## 📊 **Dashboard Features**

### **🎨 Professional Interface**
- **Modern Design**: Clean, professional layout with gradient backgrounds
- **Responsive**: Works on desktop, tablet, and mobile devices
- **Interactive**: Real-time updates and dynamic visualizations
- **User-Friendly**: Clear explanations for novice investors

### **📈 Portfolio Creation**
- **Investment Amount**: Set your budget
- **Time Horizon**: Choose short, medium, or long-term investment
- **Risk Tolerance**: Adjustable risk slider with clear explanations
- **Target Volatility**: Set your desired volatility level

### **🤖 AI Analysis**
- **Price Predictions**: ML models for asset price forecasting
- **Risk Assessment**: Advanced risk scoring and warnings
- **Sentiment Analysis**: News and social media sentiment integration
- **Technical Indicators**: AI-powered technical analysis

### **📊 Visualizations**
- **Portfolio Allocation**: Interactive pie charts
- **Performance Metrics**: Real-time performance tracking
- **Risk Metrics**: VaR, Sharpe ratio, and drawdown analysis
- **Market Insights**: Live market trends and recommendations

## 🔧 **Technical Architecture**

### **Core Components**
- **Portfolio Manager**: Central orchestrator for portfolio creation
- **Research Crew**: AI-powered asset analysis
- **Safety Officer**: Risk management and guardrails
- **Shopkeeper**: Trade execution and order management
- **Caretaker**: Portfolio rebalancing and maintenance

### **AI/ML Models**
- **Random Forest**: Price prediction and risk assessment
- **Gradient Boosting**: Enhanced portfolio optimization
- **Sentiment Analysis**: News and social media analysis
- **Technical Analysis**: RSI, MACD, and volatility indicators

### **Data Sources**
- **Yahoo Finance**: Real-time market data
- **News APIs**: Sentiment analysis data
- **Economic Indicators**: Macroeconomic data integration

## 📚 **Usage Examples**

### **Basic Portfolio Creation**
```python
from portfolio_story import PortfolioManager

# Initialize the portfolio manager
pm = PortfolioManager()

# Create a portfolio
portfolio = pm.create_portfolio(
    budget=10000,
    time_horizon='long_term',
    risk_tolerance=0.6,
    target_volatility=12
)

# Get portfolio insights
print(portfolio.get_leaderboard())
```

### **Advanced Analysis**
```python
# Run AI analysis on specific assets
analysis = pm.research_crew.analyze_assets(['AAPL', 'MSFT', 'GOOGL'])

# Get risk metrics
risk_metrics = pm.safety_officer.assess_risk(portfolio)

# Optimize portfolio
optimized = pm.optimize_portfolio(portfolio)
```

## 🧪 **Testing**

```bash
# Run the test suite
python -m pytest portfolio_story/tests/

# Run specific tests
python -m pytest portfolio_story/tests/test_portfolio_system.py
```

## 📖 **Documentation**

- **Jupyter Notebook**: `portfolio_story_demo.ipynb` - Interactive demonstration
- **API Documentation**: Built-in docstrings and type hints
- **User Guide**: Dashboard includes built-in help and explanations

## 🚀 **Deployment**

### **Local Development**
```bash
python launcher.py
```

### **Production Deployment**
```bash
# Using Gunicorn
gunicorn portfolio_story.ui.dashboard:app --bind 0.0.0.0:8050

# Using Docker
docker build -t ai-portfolio-manager .
docker run -p 8050:8050 ai-portfolio-manager
```

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 **Acknowledgments**

- **Yahoo Finance** for market data
- **Plotly** for interactive visualizations
- **Dash** for the web framework
- **Scikit-learn** for machine learning models

---

**Built with ❤️ for the future of AI-powered investing**