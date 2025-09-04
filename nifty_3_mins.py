from dhanhq import dhanhq, marketfeed
import talib
import numpy as np
import pandas as pd
import time
import datetime
import os
import logging

with open("token.txt", "r") as file:
    token = file.read()
client_id = "1102249582"
access_token = token

dhan = dhanhq(client_id, access_token)

logging.basicConfig(filename="logfile.txt", 
                    level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

SECURITY_ID = 58549  # Update as needed
IS_ACTIVE = False
IS_OPEN_POSITION = False
quantity = 0
buy_price = 0     
stop_loss = 0
COST_TO_COST_SL = False
TRAILING_SL = False
RISK = 1000
LOT_SIZE = 75  # Update as per instrument
MAX_QTY = 200  # Update as per risk management

# Helper to aggregate 1-min candles to 3-min candles
def aggregate_to_3min(df):
    df['Date'] = pd.to_datetime(df['start_Time'].apply(lambda x: dhan.convert_to_date_time(x)))
    df.set_index('Date', inplace=True)
    agg = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }
    df_3min = df.resample('3T').agg(agg).dropna().reset_index()
    return df_3min

while IS_ACTIVE is False:
    current_second = datetime.datetime.now().second
    time.sleep(1)
    print("waiting to activate", current_second)
    if current_second == 1:
        IS_ACTIVE = True

while IS_ACTIVE is True and IS_OPEN_POSITION is False:
    current_second = datetime.datetime.now().second
    if current_second == 0:
        break
    print('Active', current_second)
    time.sleep(0.15)
    intraday = dhan.intraday_daily_minute_charts(SECURITY_ID, dhan.NSE_FNO, "OPTIDX")
    if 'data' not in intraday or len(intraday['data']) < 6:
        print("Not enough data for 3-min candle aggregation.")
        continue
    intraday_df = pd.DataFrame(intraday['data'])
    df_3min = aggregate_to_3min(intraday_df)
    if len(df_3min) < 2:
        print("Not enough 3-min candles.")
        continue
    previous_closed_candle = df_3min.iloc[-2]
    current_running_candle = df_3min.iloc[-1]
    if current_running_candle['close'] > previous_closed_candle['high']:
        print('Buy')
        length_of_previous_candle = round(previous_closed_candle['high'] - previous_closed_candle['low'])
        quantity = round(round(RISK / length_of_previous_candle) / LOT_SIZE) * LOT_SIZE
        print('quantity', quantity)
        if quantity > MAX_QTY:
            quantity = MAX_QTY
        buy_price = int(current_running_candle['close'])
        stop_loss = int(previous_closed_candle['low'])
        dhan.place_order(
            security_id=SECURITY_ID,
            exchange_segment=dhan.NSE_FNO,
            transaction_type=dhan.BUY,
            quantity=quantity,
            order_type=dhan.MARKET,
            product_type=dhan.INTRA,
            price=0)
        logging.info(f"BUY at {buy_price}")
        IS_OPEN_POSITION = True
        break

while IS_OPEN_POSITION is True and quantity > 0:
    time.sleep(0.10)
    intraday = dhan.intraday_daily_minute_charts(SECURITY_ID, dhan.NSE_FNO, "OPTIDX")
    if 'data' not in intraday or len(intraday['data']) < 6:
        print("Not enough data for 3-min candle aggregation.")
        continue
    intraday_df = pd.DataFrame(intraday['data'])
    df_3min = aggregate_to_3min(intraday_df)
    if len(df_3min) < 2:
        print("Not enough 3-min candles.")
        continue
    previous_closed_candle = df_3min.iloc[-2]
    current_running_candle = df_3min.iloc[-1]
    # Stop loss
    if current_running_candle['close'] < stop_loss and COST_TO_COST_SL is False and TRAILING_SL is False:
        print("SELL")
        IS_OPEN_POSITION = False
        dhan.place_order(
            security_id=SECURITY_ID,
            exchange_segment=dhan.NSE_FNO,
            transaction_type=dhan.SELL,
            quantity=quantity,
            order_type=dhan.MARKET,
            product_type=dhan.INTRA,
            price=0)
        logging.info(f"SL hit {current_running_candle['close']}")
    # Trailing SL
    if current_running_candle['close'] < previous_closed_candle['low'] and COST_TO_COST_SL is False and TRAILING_SL is True:
        print("SELL")
        IS_OPEN_POSITION = False
        dhan.place_order(
            security_id=SECURITY_ID,
            exchange_segment=dhan.NSE_FNO,
            transaction_type=dhan.SELL,
            quantity=quantity,
            order_type=dhan.MARKET,
            product_type=dhan.INTRA,
            price=0)
        logging.info(f"Trailing SL hit {current_running_candle['close']}")
    # Shift sl to Cost to Cost
    if current_running_candle['close'] < buy_price + 1 and COST_TO_COST_SL is True and TRAILING_SL is False:
        print("SELL")
        IS_OPEN_POSITION = False
        dhan.place_order(
            security_id=SECURITY_ID,
            exchange_segment=dhan.NSE_FNO,
            transaction_type=dhan.SELL,
            quantity=quantity,
            order_type=dhan.MARKET,
            product_type=dhan.INTRA,
            price=0)
        logging.info(f"CTC SL hit {current_running_candle['close']}")
