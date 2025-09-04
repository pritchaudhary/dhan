# Nifty Option Scalping Strategy

A comprehensive and profitable automated trading strategy for Nifty options scalping with advanced risk management, detailed logging, and performance tracking.

## Features

### 🎯 **Core Strategy Features**
- **Breakout Strategy**: Identifies and trades breakouts above previous highs and below previous lows
- **Risk Management**: Configurable stop loss, target profit, and position sizing
- **Trailing Stop Loss**: Dynamic trailing stop loss to maximize profits
- **Cost-to-Cost Protection**: Automatic stop loss at entry price to minimize losses
- **Time-based Exits**: Optional time-based exit to prevent overnight positions

### 📊 **Performance Tracking**
- **Detailed Logging**: Comprehensive logs for all trades, entries, exits, and performance metrics
- **P&L Calculation**: Gross and net P&L with tax calculations
- **Win Rate Tracking**: Real-time win rate and performance statistics
- **Trade Duration**: Track how long each position is held
- **Risk Metrics**: Maximum profit/loss tracking and average performance metrics

### ⚙️ **Configuration Management**
- **Flexible Configuration**: Easy-to-modify parameters in `config.py`
- **Risk Parameters**: Configurable risk per trade, position limits, and lot sizes
- **Market Timing**: Customizable market hours and activation times
- **Technical Analysis**: Adjustable lookback periods and confirmation requirements

## Installation

1. **Install Dependencies**:
```bash
pip install dhanhq pandas numpy talib-binary
```

2. **Setup Credentials**:
   - Create a `token.txt` file with your Dhan access token
   - Update `client_id` in `config.py` if needed

3. **Configure Strategy**:
   - Modify parameters in `config.py` according to your risk appetite
   - Set appropriate strike prices and expiry dates

## Configuration

### Trading Parameters (`TRADING_CONFIG`)
```python
TRADING_CONFIG = {
    'NIFTY_STRIKE': 23600,        # ATM Strike Price
    'EXPIRY_DATE': "2025-01-09 14:30:00",  # Option expiry
    'MAX_RISK_PER_TRADE': 2000,   # Maximum risk per trade (INR)
    'MAX_QUANTITY': 300,          # Maximum quantity per trade
    'MIN_QUANTITY': 75,           # Minimum quantity (lot size)
    'LOT_SIZE': 75,               # Nifty option lot size
}
```

### Risk Management (`RISK_CONFIG`)
```python
RISK_CONFIG = {
    'USE_TRAILING_SL': True,      # Enable trailing stop loss
    'USE_COST_TO_COST': True,     # Enable cost-to-cost protection
    'USE_TARGET': True,           # Enable target profit
    'TRAILING_SL_ACTIVATION': 1.5,  # Activate trailing SL after 1.5x risk
    'TARGET_MULTIPLIER': 2.0,     # Target = 2x risk
    'STOP_LOSS_MULTIPLIER': 1.0,  # Stop loss = 1x risk
}
```

### Market Timing (`TIMING_CONFIG`)
```python
TIMING_CONFIG = {
    'MARKET_START_HOUR': 9,
    'MARKET_START_MINUTE': 15,
    'MARKET_END_HOUR': 15,
    'MARKET_END_MINUTE': 30,
    'ACTIVATION_SECOND': 1,       # Activate at second 1 of each minute
}
```

## Usage

### Basic Usage
```python
from strategy import NiftyOptionScalpingStrategy

# Initialize strategy
strategy = NiftyOptionScalpingStrategy(client_id, access_token)

# Run strategy
strategy.run_strategy()
```

### Command Line Usage
```bash
python strategy.py
```

## Strategy Logic

### Entry Conditions
1. **Breakout Above High**: Buy when current candle closes above previous candle's high
2. **Breakout Below Low**: Sell PE when current candle closes below previous candle's low
3. **Confirmation**: Optional volume confirmation and minimum breakout margin

### Exit Conditions
1. **Stop Loss**: Exit when price hits the calculated stop loss
2. **Target**: Exit when price reaches the target profit level
3. **Trailing Stop Loss**: Dynamic stop loss that moves up with price
4. **Cost-to-Cost**: Exit at entry price to minimize losses
5. **Time Exit**: Optional exit after maximum holding time

### Risk Management
- **Position Sizing**: Based on risk amount and stop loss distance
- **Risk per Trade**: Configurable maximum risk per trade
- **Lot Size Compliance**: Ensures quantities are in valid lot sizes
- **Quantity Limits**: Prevents oversized positions

## Logging and Performance

### Log Files
- `logs/nifty_scalping_YYYYMMDD.log`: Main strategy logs
- `logs/performance_YYYYMMDD.log`: Trade performance logs

### Performance Metrics Tracked
- Total trades, winning trades, losing trades
- Win rate percentage
- Total profit, total loss, net P&L
- Average profit and loss per trade
- Maximum profit and loss
- Trade duration
- ROI percentage

### Sample Log Output
```
2024-01-15 09:30:15 - INFO - Position opened: Buy 75 @ 125.50
2024-01-15 09:30:15 - INFO - Stop Loss: 120.00, Target: 131.00
2024-01-15 09:35:22 - INFO - TRADE_COMPLETED | Entry: 125.50 | Exit: 131.00 | Quantity: 75 | Gross P&L: 412.50 | Net P&L: 330.00 | ROI: 3.51% | Exit Reason: TARGET_HIT | Duration: 5.12 minutes
```

## Safety Features

### Error Handling
- Comprehensive exception handling for API calls
- Graceful handling of network issues
- Automatic retry mechanisms

### Market Hours Protection
- Only trades during market hours (9:15 AM - 3:30 PM)
- Automatic waiting during market closed periods

### Position Limits
- Maximum quantity limits to prevent oversized positions
- Minimum quantity enforcement for lot size compliance
- Risk-based position sizing

## Customization

### Adding New Entry Conditions
Modify the `analyze_market_condition` method in `strategy.py`:

```python
def analyze_market_condition(self, df: pd.DataFrame) -> Dict:
    # Add your custom entry logic here
    # Return signal dictionary with entry details
    pass
```

### Adding New Exit Conditions
Modify the `check_exit_conditions` method in `strategy.py`:

```python
def check_exit_conditions(self, current_price: float, df: pd.DataFrame) -> Tuple[bool, str]:
    # Add your custom exit logic here
    # Return (should_exit, exit_reason)
    pass
```

### Custom Indicators
Add technical indicators in the `analyze_market_condition` method:

```python
# Example: RSI indicator
rsi = talib.RSI(closes, timeperiod=14)
if rsi[-1] < 30:  # Oversold condition
    # Generate buy signal
```

## Risk Disclaimer

⚠️ **Important**: This strategy is for educational purposes only. Trading options involves significant risk of loss. Always:

1. **Paper Trade First**: Test the strategy with paper trading before live trading
2. **Start Small**: Begin with small position sizes
3. **Monitor Closely**: Always monitor automated strategies
4. **Understand Risks**: Options trading can result in 100% loss of capital
5. **Comply with Regulations**: Ensure compliance with local trading regulations

## Dependencies

- `dhanhq`: Dhan API client
- `pandas`: Data manipulation
- `numpy`: Numerical computations
- `talib`: Technical analysis indicators
- `datetime`: Time handling
- `logging`: Logging functionality

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify your API credentials
3. Ensure market data is available
4. Review configuration parameters

## License

This project is for educational purposes. Use at your own risk. 