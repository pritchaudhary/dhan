from dhanhq import dhanhq, marketfeed
import talib
import numpy as np
import pandas as pd
import time
import datetime
import os
import logging
import json
from typing import Dict, List, Optional, Tuple
from config import *

class NiftyOptionScalpingStrategyCE:
    def __init__(self, client_id: str, access_token: str):
        self.client_id = client_id
        self.access_token = access_token
        self.dhan = dhanhq(client_id, access_token)
        self.trading_config = TRADING_CONFIG
        self.risk_config = RISK_CONFIG
        self.timing_config = TIMING_CONFIG
        self.technical_config = TECHNICAL_CONFIG
        self.logging_config = LOGGING_CONFIG
        self.performance_config = PERFORMANCE_CONFIG
        self.api_config = API_CONFIG
        self.entry_config = ENTRY_CONFIG
        self.exit_config = EXIT_CONFIG
        self.IS_ACTIVE = False
        self.IS_OPEN_POSITION = False
        self.quantity = 0
        self.buy_price = 0
        self.sell_price = 0
        self.stop_loss = 0
        self.target = 0
        self.trailing_stop_loss = 0
        self.entry_time = None
        self.exit_time = None
        self.USE_TRAILING_SL = self.risk_config['USE_TRAILING_SL']
        self.USE_COST_TO_COST = self.risk_config['USE_COST_TO_COST']
        self.USE_TARGET = self.risk_config['USE_TARGET']
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0
        self.total_loss = 0
        self.max_profit = 0
        self.max_loss = 0
        self.setup_logging()
        self.load_master_list()

    def setup_logging(self):
        if self.logging_config['CREATE_LOGS_DIR'] and not os.path.exists('logs'):
            os.makedirs('logs')
        log_filename = f"logs/nifty_scalping_CE_{datetime.datetime.now().strftime('%Y%m%d')}.log"
        logging.basicConfig(
            level=getattr(logging, self.logging_config['LOG_LEVEL']),
            format=self.logging_config['LOG_FORMAT'],
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        if self.logging_config['SEPARATE_PERFORMANCE_LOG']:
            self.performance_logger = logging.getLogger('performance')
            performance_handler = logging.FileHandler(f"logs/performance_CE_{datetime.datetime.now().strftime('%Y%m%d')}.log")
            performance_handler.setFormatter(logging.Formatter(self.logging_config['PERFORMANCE_LOG_FORMAT']))
            self.performance_logger.addHandler(performance_handler)
            self.performance_logger.setLevel(logging.INFO)

    def load_master_list(self):
        try:
            logging.info("Loading master list...")
            masterlist = pd.read_csv('https://images.dhan.co/api-data/api-scrip-master.csv', nrows=1)
            masterlist = pd.read_csv('https://images.dhan.co/api-data/api-scrip-master.csv', 
                                   usecols=masterlist.columns, low_memory=False)
            self.ce_masterlist = masterlist[
                (masterlist.SEM_INSTRUMENT_NAME == 'OPTIDX') &
                (masterlist.SEM_TRADING_SYMBOL.str.startswith('NIFTY')) &
                (masterlist.SEM_EXPIRY_DATE == self.trading_config['EXPIRY_DATE']) &
                (masterlist.SEM_STRIKE_PRICE == self.trading_config['NIFTY_STRIKE']) &
                (masterlist.SEM_OPTION_TYPE == 'CE')
            ]
            if not self.ce_masterlist.empty:
                self.ce_security_id = self.ce_masterlist.iloc[0]['SEM_SMST_SECURITY_ID']
                logging.info(f"CE Security ID: {self.ce_security_id}")
            else:
                logging.error("No CE options found for the specified criteria")
        except Exception as e:
            logging.error(f"Error loading master list: {str(e)}")
            raise

    def calculate_quantity(self, risk_amount: float, stop_loss_points: int) -> int:
        if stop_loss_points <= 0:
            return self.trading_config['MIN_QUANTITY']
        quantity = round(risk_amount / stop_loss_points)
        quantity = round(quantity / self.trading_config['LOT_SIZE']) * self.trading_config['LOT_SIZE']
        quantity = max(self.trading_config['MIN_QUANTITY'], 
                      min(quantity, self.trading_config['MAX_QUANTITY']))
        return quantity

    def get_market_data(self, security_id: int) -> pd.DataFrame:
        try:
            intraday = self.dhan.intraday_daily_minute_charts(security_id, self.dhan.NSE_FNO, "OPTIDX")
            if not intraday or 'data' not in intraday:
                return pd.DataFrame()
            df = pd.DataFrame(intraday['data'])
            if df.empty:
                return df
            temp_list = []
            for i in df['start_Time']:
                temp = self.dhan.convert_to_date_time(i)
                temp_list.append(temp)
            df['Date'] = temp_list
            return df
        except Exception as e:
            logging.error(f"Error getting market data: {str(e)}")
            return pd.DataFrame()

    def analyze_market_condition(self, df: pd.DataFrame, df_15min: pd.DataFrame) -> Dict:
        if len(df) < 16 or len(df_15min) < 16:
            return {'signal': 'NO_SIGNAL', 'reason': 'Insufficient data'}
        current_candle = df.iloc[-1]
        previous_candle = df.iloc[-2]

        # 9/15 EMA trend filter on 5-min and 15-min
        ema9_5min = talib.EMA(np.array(df['close']), timeperiod=9)
        ema15_5min = talib.EMA(np.array(df['close']), timeperiod=15)
        ema9_15min = talib.EMA(np.array(df_15min['close']), timeperiod=9)
        ema15_15min = talib.EMA(np.array(df_15min['close']), timeperiod=15)
        if not (ema9_5min[-1] > ema15_5min[-1] and ema9_15min[-1] > ema15_15min[-1]):
            return {'signal': 'NO_SIGNAL', 'reason': 'No 9/15 EMA bullish alignment'}

        # Simple breakout above previous high
        if current_candle['close'] > previous_candle['high']:
            risk_points = current_candle['close'] - previous_candle['low']
            target_points = risk_points * 1.0
            return {
                'signal': 'BUY',
                'reason': '9/15 EMA bullish breakout',
                'entry_price': current_candle['close'],
                'stop_loss': previous_candle['low'],
                'target': current_candle['close'] + target_points,
                'risk_points': risk_points
            }
        return {'signal': 'NO_SIGNAL', 'reason': 'No breakout'}

    # ... (rest of the methods: place_buy_order, place_sell_order, calculate_pnl, log_trade_performance, check_exit_conditions, run_strategy, main)
    # Copy from strategy.py, but only handle CE logic

if __name__ == "__main__":
    with open(API_CONFIG['TOKEN_FILE'], "r") as file:
        access_token = file.read().strip()
    client_id = API_CONFIG['CLIENT_ID']
    strategy = NiftyOptionScalpingStrategyCE(client_id, access_token)
    strategy.run_strategy() 