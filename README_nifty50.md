# Enhanced NIFTY 50 Trading Strategy

A comprehensive and highly configurable automated trading strategy for NIFTY 50 options based on the original notebook strategy with significant enhancements and optimizations.

## 🚀 **Key Features**

### **Enhanced from Original Notebook:**
- **Object-Oriented Design**: Clean, modular, and maintainable code structure
- **Configuration-Driven**: All parameters configurable via `config_nifty50.py`
- **Advanced Technical Analysis**: RSI, EMA, Bollinger Bands, MACD, ATR
- **Comprehensive Risk Management**: Dynamic position sizing, multiple stop loss types
- **Performance Tracking**: Detailed trade history and analytics
- **Error Handling**: Robust error handling and recovery mechanisms
- **API Optimization**: Rate limiting, data caching, and efficient API usage

### **Trading Features:**
- **CE Options Trading**: Call options with breakout strategy
- **Multi-Confirmation System**: 4-point confirmation before entry
- **Dynamic Position Sizing**: Risk-based quantity calculation
- **Multiple Exit Strategies**: Stop loss, target, technical indicators
- **Market Filters**: Volume, volatility, and time-based filters
- **Daily Limits**: Maximum trades and risk per day

## 📁 **File Structure**

```
├── nifty_50.py                    # Basic enhanced strategy
├── nifty_50_enhanced.py          # Full-featured strategy with config
├── config_nifty50.py             # Configuration file
├── example_usage.py              # Usage examples
├── README_nifty50.md            # This file
└── logs/                        # Log files directory
    ├── nifty_50_enhanced_YYYYMMDD.log
    └── performance_YYYYMMDD.log
```

## ⚙️ **Configuration**

### **Trading Parameters**
```python
TRADING_CONFIG = {
    'NIFTY_PREMIUM': 25100,           # Strike price
    'EXPIRY_DATE': '2025-07-24 14:30:00',
    'RISK_PER_TRADE': 1000,           # Risk per trade (INR)
    'MAX_DAILY_TRADES': 10,           # Daily trade limit
    'MAX_DAILY_RISK': 5000,           # Daily risk limit
}
```

### **Risk Management**
```python
RISK_CONFIG = {
    'USE_TARGET': True,               # Enable take profit
    'RISK_REWARD_RATIO': 1.5,         # 1.5:1 risk-reward
    'USE_TRAILING_SL': False,         # Trailing stop loss
    'USE_COST_TO_COST': False,        # Cost-to-cost protection
}
```

### **Technical Analysis**
```python
TECHNICAL_CONFIG = {
    'RSI_PERIOD': 14,                 # RSI calculation period
    'RSI_OVERBOUGHT': 80,             # RSI overbought level
    'EMA_FAST': 9,                    # Fast EMA
    'EMA_SLOW': 21,                   # Slow EMA
    'BB_PERIOD': 20,                  # Bollinger Bands period
}
```

## 🎯 **Strategy Logic**

### **Entry Conditions (4-Point System)**
1. **Breakout**: Current close > Previous high
2. **RSI Filter**: RSI < 80 (not overbought)
3. **EMA Trend**: Fast EMA > Slow EMA
4. **Bollinger Position**: Price > Middle Bollinger Band
5. **MACD Bullish**: MACD > Signal line

**Requirement**: At least 3 out of 4 confirmations

### **Exit Conditions**
1. **Stop Loss**: Price <= Stop loss level
2. **Take Profit**: Price >= Target level
3. **RSI Overbought**: RSI > 80
4. **EMA Breakdown**: Price < Fast EMA
5. **MACD Bearish**: MACD crosses below signal

### **Risk Management**
- **Position Sizing**: Based on risk amount and stop loss distance
- **Lot Size Compliance**: Rounded to NIFTY options lot size (75)
- **Daily Limits**: Maximum trades and risk per day
- **Market Filters**: Volume, volatility, and time-based filters

## 🚀 **Quick Start**

### **1. Basic Usage**
```python
from nifty_50_enhanced import EnhancedNifty50TradingStrategy

# Run with default configuration
strategy = EnhancedNifty50TradingStrategy()
strategy.run_strategy()
```

### **2. Custom Configuration**
```python
from nifty_50_enhanced import EnhancedNifty50TradingStrategy
from config_nifty50 import *

# Modify configuration
TRADING_CONFIG['RISK_PER_TRADE'] = 2000
TECHNICAL_CONFIG['RSI_OVERBOUGHT'] = 75

# Run with custom settings
strategy = EnhancedNifty50TradingStrategy()
strategy.run_strategy()
```

### **3. Using Example Script**
```bash
python example_usage.py
```

## 📊 **Performance Tracking**

### **Metrics Tracked**
- Total trades, winning trades, losing trades
- Win rate percentage
- Total profit, total loss, net P&L
- Average win and loss per trade
- Daily trade count and P&L
- Trade history with timestamps

### **Log Files**
- **Main Log**: `logs/nifty_50_enhanced_YYYYMMDD.log`
- **Performance Log**: `logs/performance_YYYYMMDD.log`
- **Trade History**: `trade_history.json`

### **Sample Performance Output**
```
============================================================
ENHANCED NIFTY 50 TRADING STRATEGY - PERFORMANCE SUMMARY
============================================================
Total Trades: 15
Winning Trades: 9
Losing Trades: 6
Win Rate: 60.0%
Total Profit: 4500.00
Total Loss: 1800.00
Net P&L: 2700.00
Average Win: 500.00
Average Loss: 300.00
Daily Trades: 3
Daily P&L: 450.00
============================================================
```

## 🔧 **Customization**

### **Modifying Entry Conditions**
Edit `config_nifty50.py`:
```python
ENTRY_CONFIG = {
    'MIN_CONFIRMATIONS': 2,           # Require only 2 confirmations
    'TOTAL_CONDITIONS': 4,            # Total conditions to check
    'BREAKOUT_REQUIRED': True,        # Require breakout
    'VOLUME_CONFIRMATION': True,      # Require volume confirmation
}
```

### **Modifying Exit Conditions**
```python
EXIT_CONFIG = {
    'USE_STOP_LOSS': True,            # Enable stop loss
    'USE_TARGET': True,               # Enable take profit
    'USE_RSI_EXIT': True,             # Enable RSI-based exit
    'USE_EMA_EXIT': True,             # Enable EMA-based exit
    'USE_MACD_EXIT': True,            # Enable MACD-based exit
}
```

### **Modifying Risk Parameters**
```python
RISK_CONFIG = {
    'RISK_REWARD_RATIO': 2.0,         # 2:1 risk-reward ratio
    'USE_TRAILING_SL': True,          # Enable trailing stop loss
    'USE_COST_TO_COST': True,         # Enable cost-to-cost protection
}
```

## 🛡️ **Safety Features**

### **Error Handling**
- Comprehensive exception handling for API calls
- Graceful handling of network issues
- Automatic retry mechanisms
- Data validation and error recovery

### **Risk Controls**
- Daily trade and risk limits
- Position size limits
- Market condition filters
- Time-based trading restrictions

### **API Protection**
- Rate limiting to prevent API abuse
- Data caching to reduce API calls
- Connection monitoring and recovery

## 📈 **Improvements Over Original**

### **Code Quality**
- ✅ Object-oriented design
- ✅ Configuration-driven parameters
- ✅ Comprehensive error handling
- ✅ Modular and maintainable code
- ✅ Extensive logging and monitoring

### **Trading Features**
- ✅ Advanced technical indicators
- ✅ Multi-confirmation entry system
- ✅ Multiple exit strategies
- ✅ Dynamic position sizing
- ✅ Market condition filters
- ✅ Performance tracking and analytics

### **Risk Management**
- ✅ Daily limits and controls
- ✅ Multiple stop loss types
- ✅ Risk-reward ratio optimization
- ✅ Position size management
- ✅ Market timing filters

## ⚠️ **Important Notes**

1. **Paper Trading First**: Test with paper trading before live trading
2. **Configuration Review**: Review all configuration parameters
3. **Risk Management**: Never risk more than you can afford to lose
4. **Market Hours**: Strategy only trades during market hours
5. **Monitoring**: Always monitor automated strategies
6. **Backtesting**: Consider backtesting before live implementation

## 🔄 **Migration from Original**

The enhanced strategy is fully compatible with the original notebook approach but offers significant improvements:

1. **Replace** notebook cells with `nifty_50_enhanced.py`
2. **Configure** parameters in `config_nifty50.py`
3. **Run** using `python nifty_50_enhanced.py`
4. **Monitor** via log files and performance tracking

## 📞 **Support**

For issues or questions:
1. Check log files for error messages
2. Verify API credentials in `token.txt`
3. Review configuration parameters
4. Ensure market data availability
5. Check network connectivity

## 📄 **License**

This project is for educational purposes. Use at your own risk. Always comply with local trading regulations and broker terms of service.
