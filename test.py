from dhanhq import dhanhq
import talib
import numpy as np
import pandas as pd
import time


dhan = dhanhq("1102249582","eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzI1NTI0NDk5LCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMjI0OTU4MiJ9.NkNwt4fcsEiShUr1NEBOFhTJNFbLGIU8pL5yekRTMLQYZ_YrvDzZJnWl8bSiq7zaPYf4PqlBEXCtevn9K9JyFw")


# sd = dhan.intraday_daily_minute_charts("52175", dhan.NSE_FNO, "OPTIDX")

def get_data(dhan):
    fd = dhan.intraday_minute_data(
        security_id='11536',
        exchange_segment='NSE_EQ',
        instrument_type='EQUITY'
    )
    df = pd.DataFrame(fd['data'])
    print(df)

def get_exchange(dhan, exchange):
    if exchange == 'BSE':
        return dhan.BSE
    if exchange == 'NSE':
        return dhan.NSE

# def get_instrument_token():
#     df = pd.read_csv('api-scrip-master.csv')
#     data_dict = {}
#     for index , row in df.iterrows():
#         trading_symbol = row['SEM_TRADING_SYMBOL']
#         exm_exch_id = row['SEM_EXM_EXCH_ID']
#         if trading_symbol not in data_dict:
#             data_dict[trading_symbol] = {}
#         data_dict[trading_symbol][exm_exch_id ]= row.to_dict()
#     return data_dict

def get_instrument_token():
    df = pd.read_csv('api-scrip-master.csv')
    df['SEM_EXPIRY_DATE'] = pd.to_datetime(df['SEM_EXPIRY_DATE'])

    print(df)
    
    # Sort by trading symbol and expiry date
    df = df.sort_values(by=['SEM_TRADING_SYMBOL', 'SEM_EXPIRY_DATE'])
    
    data_dict = {}
    
    for symbol, group in df.groupby('SEM_TRADING_SYMBOL'):
        earliest_row = group.iloc[0]  # First row of each group will have the earliest expiry date
        trading_symbol = earliest_row['SEM_TRADING_SYMBOL']
        exm_exch_id = earliest_row['SEM_EXM_EXCH_ID']
        
        if trading_symbol not in data_dict:
            data_dict[trading_symbol] = {}
        
        data_dict[trading_symbol][exm_exch_id] = earliest_row.to_dict()
    
    return data_dict


def get_symbol_name(symbol, expiry, strike, strike_type):
    instrument = f'{symbol}-{expiry}-{str(strike)}-{strike_type}'
    return instrument


def atm_strike(spot_price):
    atm_strike = 0
    if spot_price % 100 < 25:
        atm_strike = int(spot_price / 100) * 100
    elif spot_price % 100 >= 25 or spot_price % 100 < 75:
        atm_strike = int(spot_price / 100) * 100 + 50
    else :
        atm_strike = int(spot_price / 100) * 100 + 100

    return atm_strike


nifty_ltp = 50999
symbol = 'BANKNIFTY'
expiry = 'Aug2024'
strike = atm_strike(nifty_ltp)
strike_price_ce = 'CE'
strike_price_pe = 'PE'

instrument_ce = get_symbol_name(symbol, expiry, strike, strike_price_ce)
instrument_pe = get_symbol_name(symbol, expiry, strike, strike_price_pe)

print(instrument_ce)
print(instrument_pe)

token_dict = get_instrument_token()

ce_id = token_dict[instrument_ce]['NSE']['SEM_SMST_SECURITY_ID']
pe_id = token_dict[instrument_pe]['NSE']['SEM_SMST_SECURITY_ID']


print(ce_id)
print(pe_id)

#intraday = dhan.intraday_daily_minute_charts(ce_id, dhan.NSE_FNO, "OPTIDX")

# def is_hammer(row):

#     body = abs(row['close'] - row['open'])
#     candle_range = row['high'] - row['low']
#     lower_shadow = min(row['open'], row['close']) - row['low']
#     upper_shadow = row['high'] - max(row['open'], row['close'])
    
#     return (lower_shadow > 2 * body) and (body < 0.3 * candle_range) and (upper_shadow < 0.1 * body)


# while True :
#     intraday = dhan.intraday_daily_minute_charts(51766, dhan.NSE_FNO, "OPTIDX")

#     intraday_df = pd.DataFrame(intraday['data']).tail(2)
#     temp_list = []

#     for i in intraday_df['start_Time']:
#         temp = dhan.convert_to_date_time(i)
#         temp_list.append(temp)

#     intraday_df['Date'] = temp_list

#     #print(intraday_df)
#     previous_closed_caldle = intraday_df.iloc[-2]
#     ltp = intraday_df.iloc[-1]
#     #print(previous_closed_caldle)
#     is_hammer_candle = is_hammer(previous_closed_caldle)
#     #print("current_candle : - ",ltp['close'])
#     nine_ema = talib.EMA(intraday_df['close'], timeperiod = 9)
#     fifteen_ema = talib.EMA(intraday_df['close'], timeperiod = 15)

#     open_position = False
#     # this is pull back entry
#     if is_hammer_candle is True and nine_ema > fifteen_ema and previous_closed_caldle['low'] <= nine_ema and ltp['close'] > previous_closed_caldle['high'] and open_position is False:
#         print('BUY entry places')
#         open_position = True
        
#     time.sleep(1)


    



# temp_list = []

# for i in intraday_df['start_Time']:
#     temp = dhan.convert_to_date_time(i)
#     temp_list.append(temp)

# intraday_df['Date'] = temp_list

# fast_ema = talib.EMA(intraday_df['close'], timeperiod = 9)
# slow_ema = talib.EMA(intraday_df['close'], timeperiod = 15)



#print(fast_ema)