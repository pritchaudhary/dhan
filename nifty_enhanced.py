from dhanhq import dhanhq, marketfeed
import talib
import numpy as np
import pandas as pd
import time
import datetime
import os
import logging
import threading
from collections import deque
import statistics

class EnhancedNiftyTradingStrategy:
    def __init__(self):
        # Initialize DHAN client
        with open("token.txt", "r") as file:
            token = file.read()
        
        self.client_id = "1102249582"
        self.access_token = token
        self.dhan = dhanhq(self.client_id, self.access_token)
        
        # Load master list
        self.masterlist = pd.read_csv('https://images.dhan.co/api-data/api-scrip-master.csv', nrows=1)
        self.masterlist = pd.read_csv('https://images.dhan.co/api-data/api-scrip-master.csv', 
                                    usecols=self.masterlist.columns, low_memory=False)
        
        # Setup logging
        logging.basicConfig(filename="enhanced_logfile.txt", 
                          level=logging.INFO, 
                          format="%(asctime)s - %(levelname)s - %(message)s")
        
        # Strategy parameters
        self.NIFTY_PREMIUM = 25100
        self.SECURITY_ID = 49492  # NIFTY-Jul2025-25100-CE
        
        # Trading state variables
        self.is_active = False
        self.is_open_position = False
        self.quantity = 0
        self.buy_price = 0
        self.stop_loss = 0
        self.take_profit = 0
        
        # Enhanced stop loss settings
        self.cost_to_cost_sl = False
        self.trailing_sl = False
        self.dynamic_sl = True  # New: Dynamic stop loss based on volatility
        
        # Risk management parameters
        self.risk_per_trade = 1000  # Risk amount per trade
        self.max_risk_per_day = 5000  # Maximum risk per day
        self.daily_loss_count = 0
        self.max_daily_losses = 3  # Stop trading after 3 losses
        
        # Market condition filters
        self.min_volume = 1000000  # Minimum volume filter
        self.max_spread_percent = 2.0  # Maximum spread percentage
        self.volatility_threshold = 0.02  # Minimum volatility threshold
        
        # Technical indicators parameters
        self.rsi_period = 14
        self.ema_fast = 9
        self.ema_slow = 21
        self.bb_period = 20
        self.bb_std = 2
        
        # API rate limiting
        self.last_api_call = 0
        self.min_api_interval = 0.1  # 10 requests per second = 0.1 second interval
        
        # Data cache for optimization
        self.data_cache = deque(maxlen=10)  # Keep last 10 data points
        self.cache_valid_seconds = 3  # Cache valid for 3 seconds
        
        # Performance tracking
        self.trade_history = []
        self.win_rate = 0
        self.avg_win = 0
        self.avg_loss = 0
        
    def rate_limit_api_call(self):
        """Ensure API calls respect rate limits"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        
        if time_since_last_call < self.min_api_interval:
            sleep_time = self.min_api_interval - time_since_last_call
            time.sleep(sleep_time)
        
        self.last_api_call = time.time()
    
    def get_intraday_data(self, lookback_periods=50):
        """Get intraday data with caching and rate limiting"""
        current_time = time.time()
        
        # Check if we have recent cached data
        if (self.data_cache and 
            current_time - self.data_cache[-1]['timestamp'] < self.cache_valid_seconds):
            return self.data_cache[-1]['data']
        
        # Make API call with rate limiting
        self.rate_limit_api_call()
        
        try:
            intraday = self.dhan.intraday_daily_minute_charts(
                self.SECURITY_ID, self.dhan.NSE_FNO, "OPTIDX")
            
            if intraday.get('status') == 'success' and 'data' in intraday:
                # Cache the data
                self.data_cache.append({
                    'data': intraday,
                    'timestamp': current_time
                })
                return intraday
            else:
                logging.error(f"API Error: {intraday}")
                return None
                
        except Exception as e:
            logging.error(f"API call failed: {e}")
            return None
    
    def calculate_technical_indicators(self, df):
        """Calculate technical indicators for better entry/exit decisions"""
        try:
            if len(df) < max(self.rsi_period, self.ema_slow, self.bb_period):
                return None
            
            # Convert to numpy arrays for talib
            high = np.array(df['high'], dtype=float)
            low = np.array(df['low'], dtype=float)
            close = np.array(df['close'], dtype=float)
            volume = np.array(df['volume'], dtype=float)
            
            indicators = {}
            
            # RSI
            indicators['rsi'] = talib.RSI(close, timeperiod=self.rsi_period)
            
            # EMAs
            indicators['ema_fast'] = talib.EMA(close, timeperiod=self.ema_fast)
            indicators['ema_slow'] = talib.EMA(close, timeperiod=self.ema_slow)
            
            # Bollinger Bands
            indicators['bb_upper'], indicators['bb_middle'], indicators['bb_lower'] = talib.BBANDS(
                close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std)
            
            # ATR for volatility
            indicators['atr'] = talib.ATR(high, low, close, timeperiod=14)
            
            # Volume indicators
            indicators['volume_sma'] = talib.SMA(volume, timeperiod=20)
            
            # MACD
            indicators['macd'], indicators['macd_signal'], indicators['macd_hist'] = talib.MACD(close)
            
            return indicators
            
        except Exception as e:
            logging.error(f"Technical indicators calculation error: {e}")
            return None
    
    def check_market_conditions(self, df, indicators):
        """Check if market conditions are favorable for trading"""
        try:
            if df is None or len(df) < 5:
                return False, "Insufficient data"
            
            current_candle = df.iloc[-1]
            
            # Volume filter
            if current_candle['volume'] < self.min_volume:
                return False, "Low volume"
            
            # Volatility filter
            if indicators and len(indicators['atr']) > 0:
                current_atr = indicators['atr'][-1]
                if current_atr / current_candle['close'] < self.volatility_threshold:
                    return False, "Low volatility"
            
            # Spread filter (approximate)
            spread = (current_candle['high'] - current_candle['low']) / current_candle['close'] * 100
            if spread > self.max_spread_percent:
                return False, "High spread"
            
            return True, "Good market conditions"
            
        except Exception as e:
            logging.error(f"Market conditions check error: {e}")
            return False, f"Error: {e}"
    
    def check_enhanced_buy_condition(self, df, indicators):
        """Enhanced buy condition with multiple confirmations"""
        try:
            if df is None or len(df) < 3 or indicators is None:
                return False, "Insufficient data"
            
            current_candle = df.iloc[-1]
            previous_candle = df.iloc[-2]
            prev_prev_candle = df.iloc[-3]
            
            # Basic breakout condition (original)
            breakout_condition = current_candle['close'] > previous_candle['high']
            
            # Additional confirmations
            confirmations = 0
            total_conditions = 6
            
            # 1. RSI not overbought
            if len(indicators['rsi']) > 0 and indicators['rsi'][-1] < 70:
                confirmations += 1
            
            # 2. EMA trend confirmation
            if (len(indicators['ema_fast']) > 0 and len(indicators['ema_slow']) > 0 and
                indicators['ema_fast'][-1] > indicators['ema_slow'][-1]):
                confirmations += 1
            
            # 3. Volume confirmation
            if (len(indicators['volume_sma']) > 0 and 
                current_candle['volume'] > indicators['volume_sma'][-1] * 1.2):
                confirmations += 1
            
            # 4. MACD bullish
            if (len(indicators['macd']) > 0 and len(indicators['macd_signal']) > 0 and
                indicators['macd'][-1] > indicators['macd_signal'][-1]):
                confirmations += 1
            
            # 5. Price above Bollinger middle
            if (len(indicators['bb_middle']) > 0 and 
                current_candle['close'] > indicators['bb_middle'][-1]):
                confirmations += 1
            
            # 6. Consecutive higher lows
            if (previous_candle['low'] > prev_prev_candle['low'] and 
                current_candle['low'] > previous_candle['low']):
                confirmations += 1
            
            # Require at least 4 out of 6 confirmations
            if breakout_condition and confirmations >= 4:
                return True, f"Buy confirmed with {confirmations}/{total_conditions} signals"
            
            return False, f"Only {confirmations}/{total_conditions} confirmations"
            
        except Exception as e:
            logging.error(f"Enhanced buy condition check error: {e}")
            return False, f"Error: {e}"
    
    def calculate_dynamic_stop_loss(self, df, indicators, buy_price):
        """Calculate dynamic stop loss based on volatility and support levels"""
        try:
            if df is None or len(df) < 5:
                return buy_price * 0.98  # 2% stop loss as fallback
            
            # Method 1: ATR-based stop loss
            if indicators and len(indicators['atr']) > 0:
                atr_stop = buy_price - (indicators['atr'][-1] * 2)
            else:
                atr_stop = buy_price * 0.98
            
            # Method 2: Support level stop loss
            recent_lows = [df.iloc[i]['low'] for i in range(-5, 0)]
            support_level = min(recent_lows)
            support_stop = support_level * 0.995  # 0.5% below support
            
            # Method 3: Bollinger lower band stop
            if indicators and len(indicators['bb_lower']) > 0:
                bb_stop = indicators['bb_lower'][-1]
            else:
                bb_stop = buy_price * 0.97
            
            # Use the most conservative (highest) stop loss
            dynamic_stop = max(atr_stop, support_stop, bb_stop)
            
            # Ensure stop loss is not too tight (minimum 1% from buy price)
            min_stop = buy_price * 0.99
            dynamic_stop = max(dynamic_stop, min_stop)
            
            return dynamic_stop
            
        except Exception as e:
            logging.error(f"Dynamic stop loss calculation error: {e}")
            return buy_price * 0.98
    
    def calculate_take_profit(self, buy_price, stop_loss):
        """Calculate take profit based on risk-reward ratio"""
        try:
            risk = buy_price - stop_loss
            # Use 2:1 risk-reward ratio
            take_profit = buy_price + (risk * 2)
            return take_profit
        except Exception as e:
            logging.error(f"Take profit calculation error: {e}")
            return buy_price * 1.04  # 4% take profit as fallback
    
    def check_enhanced_sell_conditions(self, df, indicators):
        """Enhanced sell conditions with multiple exit strategies"""
        try:
            if df is None or len(df) < 2:
                return False, "No data"
            
            current_candle = df.iloc[-1]
            previous_candle = df.iloc[-2]
            
            # 1. Stop Loss
            if current_candle['close'] < self.stop_loss:
                return True, "Stop Loss Hit", current_candle
            
            # 2. Take Profit
            if current_candle['close'] >= self.take_profit:
                return True, "Take Profit Hit", current_candle
            
            # 3. RSI Overbought
            if (indicators and len(indicators['rsi']) > 0 and 
                indicators['rsi'][-1] > 80):
                return True, "RSI Overbought", current_candle
            
            # 4. Price below EMA fast
            if (indicators and len(indicators['ema_fast']) > 0 and 
                current_candle['close'] < indicators['ema_fast'][-1]):
                return True, "Below EMA Fast", current_candle
            
            # 5. MACD bearish crossover
            if (indicators and len(indicators['macd']) > 0 and len(indicators['macd_signal']) > 0 and
                indicators['macd'][-1] < indicators['macd_signal'][-1] and
                indicators['macd'][-2] >= indicators['macd_signal'][-2]):
                return True, "MACD Bearish Crossover", current_candle
            
            # 6. Price below Bollinger middle
            if (indicators and len(indicators['bb_middle']) > 0 and 
                current_candle['close'] < indicators['bb_middle'][-1]):
                return True, "Below Bollinger Middle", current_candle
            
            return False, "Hold position"
            
        except Exception as e:
            logging.error(f"Enhanced sell condition check error: {e}")
            return False, f"Error: {e}"
    
    def calculate_position_size(self, risk_amount, stop_loss_price, buy_price):
        """Calculate position size based on risk management"""
        try:
            risk_per_share = buy_price - stop_loss_price
            if risk_per_share <= 0:
                return 75  # Default quantity
            
            # Calculate quantity based on risk
            calculated_quantity = int(risk_amount / risk_per_share)
            
            # Round to nearest lot size (75 for NIFTY options)
            lot_size = 75
            quantity = (calculated_quantity // lot_size) * lot_size
            
            # Apply limits
            quantity = max(quantity, lot_size)  # Minimum 1 lot
            quantity = min(quantity, 300)  # Maximum 4 lots
            
            return quantity
            
        except Exception as e:
            logging.error(f"Position size calculation error: {e}")
            return 75  # Default quantity
    
    def update_performance_metrics(self, trade_result):
        """Update performance tracking metrics"""
        try:
            self.trade_history.append(trade_result)
            
            if len(self.trade_history) >= 10:  # Calculate metrics after 10 trades
                wins = [t for t in self.trade_history if t['pnl'] > 0]
                losses = [t for t in self.trade_history if t['pnl'] < 0]
                
                self.win_rate = len(wins) / len(self.trade_history) * 100
                
                if wins:
                    self.avg_win = sum(t['pnl'] for t in wins) / len(wins)
                if losses:
                    self.avg_loss = sum(t['pnl'] for t in losses) / len(losses)
                
                logging.info(f"Performance Update - Win Rate: {self.win_rate:.1f}%, "
                           f"Avg Win: {self.avg_win:.2f}, Avg Loss: {self.avg_loss:.2f}")
            
        except Exception as e:
            logging.error(f"Performance metrics update error: {e}")
    
    def should_stop_trading(self):
        """Check if we should stop trading for the day"""
        if self.daily_loss_count >= self.max_daily_losses:
            return True, "Maximum daily losses reached"
        
        # Check if we've exceeded daily risk limit
        today_trades = [t for t in self.trade_history 
                       if t['timestamp'].date() == datetime.date.today()]
        today_losses = sum(t['pnl'] for t in today_trades if t['pnl'] < 0)
        
        if abs(today_losses) >= self.max_risk_per_day:
            return True, "Daily risk limit exceeded"
        
        return False, "Continue trading"
    
    def process_candle_data(self, intraday_data):
        """Process candle data and return DataFrame"""
        if not intraday_data:
            return None
            
        try:
            # Create DataFrame from the dictionary of lists
            intraday_df = pd.DataFrame(intraday_data['data'])
            
            # Convert timestamps
            temp_list = []
            for i in intraday_df['start_Time']:
                temp = self.dhan.convert_to_date_time(i)
                temp_list.append(temp)
            
            intraday_df['Date'] = temp_list
            
            return intraday_df
            
        except Exception as e:
            logging.error(f"Data processing error: {e}")
            return None
    
    def wait_for_activation(self):
        """Wait for the right second to activate strategy"""
        print("Waiting for activation...")
        while not self.is_active:
            current_second = datetime.datetime.now().second
            print(f"Waiting to activate - Current second: {current_second}")
            time.sleep(1)
            if current_second == 1:  # Activate at second 1
                self.is_active = True
                print("Strategy activated!")
    
    def execute_buy_order(self, df, indicators):
        """Execute buy order with enhanced logic"""
        try:
            current_candle = df.iloc[-1]
            self.buy_price = int(current_candle['close'])
            
            # Calculate dynamic stop loss
            self.stop_loss = self.calculate_dynamic_stop_loss(df, indicators, self.buy_price)
            
            # Calculate take profit
            self.take_profit = self.calculate_take_profit(self.buy_price, self.stop_loss)
            
            # Calculate position size
            self.quantity = self.calculate_position_size(
                self.risk_per_trade, self.stop_loss, self.buy_price)
            
            print(f"Executing BUY order - Quantity: {self.quantity}, Price: {self.buy_price}")
            print(f"Stop Loss: {self.stop_loss:.2f}, Take Profit: {self.take_profit:.2f}")
            
            # Execute order with rate limiting
            self.rate_limit_api_call()
            
            order_result = self.dhan.place_order(
                security_id=self.SECURITY_ID,
                exchange_segment=self.dhan.NSE_FNO,
                transaction_type=self.dhan.BUY,
                quantity=self.quantity,
                order_type=self.dhan.MARKET,
                product_type=self.dhan.INTRA,
                price=0
            )
            
            logging.info(f"BUY order placed at {self.buy_price} - Result: {order_result}")
            self.is_open_position = True
            
            return True
            
        except Exception as e:
            logging.error(f"Buy order execution failed: {e}")
            return False
    
    def execute_sell_order(self, sell_reason, current_candle):
        """Execute sell order with enhanced logic"""
        try:
            sell_price = int(current_candle['close'])
            pnl = (sell_price - self.buy_price) * self.quantity
            
            print(f"Executing SELL order - Reason: {sell_reason}")
            print(f"Sell Price: {sell_price}, P&L: {pnl:.2f}")
            
            # Execute order with rate limiting
            self.rate_limit_api_call()
            
            order_result = self.dhan.place_order(
                security_id=self.SECURITY_ID,
                exchange_segment=self.dhan.NSE_FNO,
                transaction_type=self.dhan.SELL,
                quantity=self.quantity,
                order_type=self.dhan.MARKET,
                product_type=self.dhan.INTRA,
                price=0
            )
            
            # Record trade result
            trade_result = {
                'timestamp': datetime.datetime.now(),
                'buy_price': self.buy_price,
                'sell_price': sell_price,
                'quantity': self.quantity,
                'pnl': pnl,
                'reason': sell_reason
            }
            
            self.update_performance_metrics(trade_result)
            
            if pnl < 0:
                self.daily_loss_count += 1
            
            logging.info(f"SELL order placed - Reason: {sell_reason}, P&L: {pnl:.2f} - Result: {order_result}")
            
            self.is_open_position = False
            self.quantity = 0
            
            return True
            
        except Exception as e:
            logging.error(f"Sell order execution failed: {e}")
            return False
    
    def run_buy_phase(self):
        """Run the enhanced buy phase"""
        print("Starting enhanced buy phase...")
        
        while self.is_active and not self.is_open_position:
            # Check if we should stop trading
            should_stop, reason = self.should_stop_trading()
            if should_stop:
                print(f"Stopping trading: {reason}")
                break
            
            current_second = datetime.datetime.now().second
            if current_second == 0:  # Exit at second 0
                break
                
            print(f'Active - Current second: {current_second}')
            
            # Get data with caching
            intraday_data = self.get_intraday_data()
            if not intraday_data:
                time.sleep(0.1)
                continue
            
            # Process data
            df = self.process_candle_data(intraday_data)
            if df is None or len(df) < 20:
                time.sleep(0.1)
                continue
            
            # Calculate technical indicators
            indicators = self.calculate_technical_indicators(df)
            if indicators is None:
                time.sleep(0.1)
                continue
            
            # Check market conditions
            market_ok, market_reason = self.check_market_conditions(df, indicators)
            if not market_ok:
                print(f"Market conditions not favorable: {market_reason}")
                time.sleep(0.1)
                continue
            
            # Check enhanced buy condition
            buy_condition_met, buy_reason = self.check_enhanced_buy_condition(df, indicators)
            
            if buy_condition_met:
                print(f"Buy condition met: {buy_reason}")
                # Execute buy order immediately
                if self.execute_buy_order(df, indicators):
                    print("Buy order executed successfully!")
                    break
                else:
                    print("Buy order failed, continuing...")
            else:
                print(f"Buy condition not met: {buy_reason}")
            
            # Small delay to prevent excessive API calls
            time.sleep(0.1)
    
    def run_sell_phase(self):
        """Run the enhanced sell phase"""
        print("Starting enhanced sell phase...")
        
        while self.is_open_position and self.quantity > 0:
            # Get data with caching
            intraday_data = self.get_intraday_data()
            if not intraday_data:
                time.sleep(0.1)
                continue
            
            # Process data
            df = self.process_candle_data(intraday_data)
            if df is None or len(df) < 20:
                time.sleep(0.1)
                continue
            
            # Calculate technical indicators
            indicators = self.calculate_technical_indicators(df)
            if indicators is None:
                time.sleep(0.1)
                continue
            
            # Check enhanced sell conditions
            sell_condition_met, sell_reason, current_candle = self.check_enhanced_sell_conditions(df, indicators)
            
            if sell_condition_met:
                # Execute sell order immediately
                if self.execute_sell_order(sell_reason, current_candle):
                    print("Sell order executed successfully!")
                    break
                else:
                    print("Sell order failed, continuing...")
            
            print("Monitoring position...")
            time.sleep(0.1)
    
    def run_strategy(self):
        """Main enhanced strategy execution"""
        try:
            print("Starting Enhanced Nifty Trading Strategy...")
            print(f"Target Security ID: {self.SECURITY_ID}")
            print(f"Strike Price: {self.NIFTY_PREMIUM}")
            print(f"Risk per trade: {self.risk_per_trade}")
            print(f"Max daily losses: {self.max_daily_losses}")
            
            # Phase 1: Wait for activation
            self.wait_for_activation()
            
            # Phase 2: Buy phase
            self.run_buy_phase()
            
            # Phase 3: Sell phase (if position opened)
            if self.is_open_position:
                self.run_sell_phase()
            
            print("Strategy execution completed.")
            print(f"Final Performance - Win Rate: {self.win_rate:.1f}%")
            
        except KeyboardInterrupt:
            print("Strategy interrupted by user.")
            logging.info("Strategy interrupted by user.")
        except Exception as e:
            print(f"Strategy execution failed: {e}")
            logging.error(f"Strategy execution failed: {e}")

def main():
    """Main function to run the enhanced strategy"""
    strategy = EnhancedNiftyTradingStrategy()
    strategy.run_strategy()

if __name__ == "__main__":
    main()
