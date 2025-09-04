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

class NiftyTradingStrategy:
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
        logging.basicConfig(filename="logfile.txt", 
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
        
        # Stop loss settings
        self.cost_to_cost_sl = False
        self.trailing_sl = False
        
        # API rate limiting
        self.last_api_call = 0
        self.min_api_interval = 0.1  # 10 requests per second = 0.1 second interval
        
        # Data cache for optimization
        self.data_cache = deque(maxlen=5)  # Keep last 5 data points
        self.cache_valid_seconds = 5  # Cache valid for 5 seconds
        
    def rate_limit_api_call(self):
        """Ensure API calls respect rate limits"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        
        if time_since_last_call < self.min_api_interval:
            sleep_time = self.min_api_interval - time_since_last_call
            time.sleep(sleep_time)
        
        self.last_api_call = time.time()
    
    def get_intraday_data(self):
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
    
    def process_candle_data(self, intraday_data):
        """Process candle data and return DataFrame"""
        if not intraday_data:
            return None
            
        try:
            # Create DataFrame from the dictionary of lists
            intraday_df = pd.DataFrame(intraday_data['data']).tail(2)
            
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
    
    def check_buy_condition(self, intraday_df):
        """Check if buy condition is met"""
        if intraday_df is None or len(intraday_df) < 2:
            return False
            
        try:
            previous_closed_candle = intraday_df.iloc[-2]
            current_running_candle = intraday_df.iloc[-1]
            
            # Original condition was commented out, using simplified logic
            # if current_running_candle['close'] > previous_closed_candle['high']:
            
            # For now, using the simplified buy logic from notebook
            print('Buy condition met')
            return True, previous_closed_candle, current_running_candle
            
        except Exception as e:
            logging.error(f"Buy condition check error: {e}")
            return False, None, None
    
    def execute_buy_order(self, previous_candle, current_candle):
        """Execute buy order with precise timing"""
        try:
            # Calculate position size
            length_of_previous_candle = round(previous_candle['high'] - previous_candle['low'])
            risk = 1000
            self.quantity = 75  # Simplified from notebook
            
            if self.quantity > 200:
                self.quantity = 200
            
            self.buy_price = int(current_candle['close'])
            self.stop_loss = int(previous_candle['low'])
            
            print(f"Executing BUY order - Quantity: {self.quantity}, Price: {self.buy_price}")
            
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
    
    def check_sell_conditions(self, intraday_df):
        """Check all sell conditions"""
        if intraday_df is None or len(intraday_df) < 2:
            return False, "No data"
            
        try:
            previous_closed_candle = intraday_df.iloc[-2]
            current_running_candle = intraday_df.iloc[-1]
            
            # Stop loss condition
            if (current_running_candle['close'] < self.stop_loss and 
                not self.cost_to_cost_sl and not self.trailing_sl):
                return True, "Stop Loss", current_running_candle
            
            # Trailing SL condition
            if (current_running_candle['close'] < previous_closed_candle['low'] and 
                not self.cost_to_cost_sl and self.trailing_sl):
                return True, "Trailing SL", current_running_candle
            
            # Cost to Cost SL condition
            if (current_running_candle['close'] < self.buy_price + 1 and 
                self.cost_to_cost_sl and not self.trailing_sl):
                return True, "Cost to Cost SL", current_running_candle
            
            return False, "No sell condition met"
            
        except Exception as e:
            logging.error(f"Sell condition check error: {e}")
            return False, f"Error: {e}"
    
    def execute_sell_order(self, sell_reason, current_candle):
        """Execute sell order with precise timing"""
        try:
            print(f"Executing SELL order - Reason: {sell_reason}")
            
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
            
            logging.info(f"SELL order placed - Reason: {sell_reason}, Price: {current_candle['close']} - Result: {order_result}")
            self.is_open_position = False
            self.quantity = 0
            
            return True
            
        except Exception as e:
            logging.error(f"Sell order execution failed: {e}")
            return False
    
    def run_buy_phase(self):
        """Run the buy phase with optimized timing"""
        print("Starting buy phase...")
        
        while self.is_active and not self.is_open_position:
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
            intraday_df = self.process_candle_data(intraday_data)
            if intraday_df is None:
                time.sleep(0.1)
                continue
            
            # Check buy condition
            buy_condition_met, previous_candle, current_candle = self.check_buy_condition(intraday_df)
            
            if buy_condition_met:
                # Execute buy order immediately
                if self.execute_buy_order(previous_candle, current_candle):
                    print("Buy order executed successfully!")
                    break
                else:
                    print("Buy order failed, continuing...")
            
            # Small delay to prevent excessive API calls
            time.sleep(0.1)
    
    def run_sell_phase(self):
        """Run the sell phase with optimized timing"""
        print("Starting sell phase...")
        
        while self.is_open_position and self.quantity > 0:
            # Get data with caching
            intraday_data = self.get_intraday_data()
            if not intraday_data:
                time.sleep(0.1)
                continue
            
            # Process data
            intraday_df = self.process_candle_data(intraday_data)
            if intraday_df is None:
                time.sleep(0.1)
                continue
            
            # Check sell conditions
            sell_condition_met, sell_reason, current_candle = self.check_sell_conditions(intraday_df)
            
            if sell_condition_met:
                # Execute sell order immediately
                if self.execute_sell_order(sell_reason, current_candle):
                    print("Sell order executed successfully!")
                    break
                else:
                    print("Sell order failed, continuing...")
            
            print("Waiting for sell condition...")
            time.sleep(0.1)
    
    def run_strategy(self):
        """Main strategy execution"""
        try:
            print("Starting Nifty Trading Strategy...")
            print(f"Target Security ID: {self.SECURITY_ID}")
            print(f"Strike Price: {self.NIFTY_PREMIUM}")
            
            # Phase 1: Wait for activation
            self.wait_for_activation()
            
            # Phase 2: Buy phase
            self.run_buy_phase()
            
            # Phase 3: Sell phase (if position opened)
            if self.is_open_position:
                self.run_sell_phase()
            
            print("Strategy execution completed.")
            
        except KeyboardInterrupt:
            print("Strategy interrupted by user.")
            logging.info("Strategy interrupted by user.")
        except Exception as e:
            print(f"Strategy execution failed: {e}")
            logging.error(f"Strategy execution failed: {e}")

def main():
    """Main function to run the strategy"""
    strategy = NiftyTradingStrategy()
    strategy.run_strategy()

if __name__ == "__main__":
    main()
