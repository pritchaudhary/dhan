from dhanhq import dhanhq, marketfeed
import talib
from talib import MA_Type
import numpy as np
import pandas as pd
import time

dhan = dhanhq("1102249582","eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzI1NTI0NDk5LCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMjI0OTU4MiJ9.NkNwt4fcsEiShUr1NEBOFhTJNFbLGIU8pL5yekRTMLQYZ_YrvDzZJnWl8bSiq7zaPYf4PqlBEXCtevn9K9JyFw")

SECURITY_ID = "58440"
instruments = [(2, SECURITY_ID)]  # here 2 for FNO and 51766 is for instrument id
subscription_code = marketfeed.Ticker
ltp = 0 


# Add your Dhan Client ID and Access Token
client_id = "1102249582"
access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzI1NTI0NDk5LCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMjI0OTU4MiJ9.NkNwt4fcsEiShUr1NEBOFhTJNFbLGIU8pL5yekRTMLQYZ_YrvDzZJnWl8bSiq7zaPYf4PqlBEXCtevn9K9JyFw"

# Define custom settings for Bollinger Band
timeperiod = 20
nbdevup = 1.5  # Multiplier for the upper band
nbdevdn = 1.5  # Multiplier for the lower band
matype = 0     # Simple Moving Average

def is_hammer(row):
    
    body = abs(row['close'] - row['open'])
    candle_range = row['high'] - row['low']
    lower_shadow = min(row['open'], row['close']) - row['low']
    upper_shadow = row['high'] - max(row['open'], row['close'])

    
    #return (lower_shadow > 2 * body) and (body < 0.3 * candle_range) and (upper_shadow < 0.1 * body)
    return (lower_shadow > body) and (upper_shadow <  body)

def get_one_minute_chart() :
    intraday = dhan.intraday_daily_minute_charts(SECURITY_ID, dhan.NSE_FNO, "OPTIDX")
    intraday_df = pd.DataFrame(intraday['data']).tail(2)

    temp_list = []

    for i in intraday_df['start_Time']:
        temp = dhan.convert_to_date_time(i)
        temp_list.append(temp)

    intraday_df['Date'] = temp_list
    print(intraday_df)

        #print(intraday_df)
    previous_closed_candle = intraday_df.iloc[-2]
    ltp = intraday_df.iloc[-1]
    #print(previous_closed_candle)
    is_hammer_candle = is_hammer(previous_closed_candle) # type: ignore
      #print("current_candle : - ",ltp['close'])
    nine_ema = talib.EMA(intraday_df['close'], timeperiod = 9)
    fifteen_ema = talib.EMA(intraday_df['close'], timeperiod = 15)
    # Calculate Bollinger Bands
    upperband, middleband, lowerband = talib.BBANDS(
        intraday_df['close'],
        timeperiod=timeperiod,
        nbdevup=nbdevup,
        nbdevdn=nbdevdn,
        matype=matype
    )

    # if is_hammer_candle and ltp > previous_closed_candle['high'] and ltp < nine_ema and ltp < fifteen_ema and previous_closed_candle['close']< lowerband:
    #     print("Buy")

    # if is_hammer_candle and (previous_closed_candle['low'] <= nine_ema or previous_closed_candle <= fifteen_ema):
    #     print("Buy by trend")

    if is_hammer_candle and ltp > previous_closed_candle['high'] and ltp < nine_ema and ltp < fifteen_ema and previous_closed_candle['close'] < lowerband:
        print("Buy")

    if is_hammer_candle and (previous_closed_candle['low'] <= nine_ema or previous_closed_candle['low'] <= fifteen_ema):
        print("Buy by trend")

  


while True:
    get_one_minute_chart()
    time.sleep(1) 

# async def on_connect(instance):
#     print("Connected to websocket")

# async def on_message(instance, message):
#     current_second = datetime.datetime.now().second # this is to check if one minute completed
#     ltp = message.get('LTP')
#     if current_second == 1:
#         get_one_minute_chart()
#     print("Received:", message)
    


# feed = marketfeed.DhanFeed(client_id,
#     access_token,
#     instruments,
#     subscription_code,
#     on_connect=on_connect,
#     on_message=on_message)

# feed.run_forever()







