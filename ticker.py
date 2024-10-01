from dhanhq import marketfeed
import datetime
from dhanhq import dhanhq
import talib
import numpy as np
import pandas as pd
import time





# Add your Dhan Client ID and Access Token
client_id = "1102249582"
access_token = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

dhan = dhanhq(client_id,access_token)

SECURITY_ID = "64209"

ltp = 0 
instruments = [(2, SECURITY_ID)]  # here 2 for FNO and 51766 is for instrument id

# Type of data subscription
subscription_code = marketfeed.Ticker

# Ticker - Ticker Data
# Quote - Quote Data
# Depth - Market Depth


# def is_hammer(row):
    
#     body = abs(row['close'] - row['open'])
#     candle_range = row['high'] - row['low']
#     lower_shadow = min(row['open'], row['close']) - row['low']
#     upper_shadow = row['high'] - max(row['open'], row['close'])

    
#     #return (lower_shadow > 2 * body) and (body < 0.3 * candle_range) and (upper_shadow < 0.1 * body)
#     return (lower_shadow > body) and (upper_shadow <  body)


# def get_one_minute_chart(ltp):
#     intraday = dhan.intraday_daily_minute_charts(SECURITY_ID, dhan.NSE_FNO, "OPTIDX")

#     intraday_df = pd.DataFrame(intraday['data']).tail(2)
#     # temp_list = []

#     # for i in intraday_df['start_Time']:
#     #     temp = dhan.convert_to_date_time(i)
#     #     temp_list.append(temp)

#     # intraday_df['Date'] = temp_list

#     #print(intraday_df)
#     previous_closed_caldle = intraday_df.iloc[-2]
#     ltp = intraday_df.iloc[-1]
#     #print(previous_closed_caldle)
#     is_hammer_candle = is_hammer(previous_closed_caldle)
#     if is_hammer_candle:
#         print("is_hammer_candle   : --- ", is_hammer_candle)

# def indicators():
#     fast_ema = talib.EMA(intraday_df['close'], timeperiod = 9)
#     slow_ema = talib.EMA(intraday_df['close'], timeperiod = 15)


async def on_connect(instance):
    print("Connected to websocket")

async def on_message(instance, message):
    # current_second = datetime.datetime.now().second # this is to check if one minute completed
    # ltp = message.get('LTP')
    # if current_second == 1:
    #     get_one_minute_chart(ltp)
    print("Received:", message)
    

print("Subscription code :", subscription_code)

feed = marketfeed.DhanFeed(client_id,
    access_token,
    instruments,
    subscription_code,
    on_connect=on_connect,
    on_message=on_message)

feed.run_forever()