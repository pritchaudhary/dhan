from dhanhq import dhanhq, marketfeed
import talib
import numpy as np
import pandas as pd
import time
import datetime
import os
import logging

"""
NIFTY 50 Options Trading Strategy
Replicated from self_strategy_nifty_fifty.ipynb

DhanHQ API Rate Limits (https://dhanhq.co/docs/v1/#rate-limit):
- Order APIs: 25/sec, 250/min, 1000/hour, 7000/day
- Data APIs: 10/sec, 1000/min, 5000/hour, 10000/day
- Non Trading APIs: 20/sec, Unlimited/min
"""

# Load token and initialize DHAN client
with open("token.txt", "r") as file:
    token = file.read()

client_id = "1102249582"
access_token = token
dhan = dhanhq(client_id, access_token)

# Load master list
masterlist = pd.read_csv('https://images.dhan.co/api-data/api-scrip-master.csv', nrows=1)
masterlist = pd.read_csv('https://images.dhan.co/api-data/api-scrip-master.csv', 
                        usecols=masterlist.columns, low_memory=False)

# Setup logging
logging.basicConfig(filename="logfile.txt", 
                    level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Configuration parameters
NIFTY_PREMIUM = 25750
EXPIRY_DATE = '2025-10-28 14:30:00'

# OPTION TYPE CONFIGURATION
# Set to 'CE' for Call Options or 'PE' for Put Options
OPTION_TYPE = 'PE'  # Change this to 'PE' if you want to trade Put options

# Filter CE options
filtered_ce_masterlist = masterlist[
    (masterlist.SEM_INSTRUMENT_NAME == 'OPTIDX') &
    (masterlist.SEM_TRADING_SYMBOL.str.startswith('NIFTY')) &
    (masterlist.SEM_EXPIRY_DATE == EXPIRY_DATE) &
    (masterlist.SEM_STRIKE_PRICE == NIFTY_PREMIUM) &
    (masterlist.SEM_OPTION_TYPE == 'CE') 
]

# Filter PE options
filtered_pe_masterlist = masterlist[
    (masterlist.SEM_INSTRUMENT_NAME == 'OPTIDX') &
    (masterlist.SEM_TRADING_SYMBOL.str.startswith('NIFTY')) &
    (masterlist.SEM_EXPIRY_DATE == EXPIRY_DATE) &
    (masterlist.SEM_STRIKE_PRICE == NIFTY_PREMIUM) &
    (masterlist.SEM_OPTION_TYPE == 'PE')
]

# Get security IDs
print("\n" + "="*60)
print("NIFTY 50 OPTIONS TRADING STRATEGY")
print("="*60)
print(f"Strike Price: {NIFTY_PREMIUM}")
print(f"Expiry Date: {EXPIRY_DATE}")
print(f"Option Type: {OPTION_TYPE} ({'Call Options' if OPTION_TYPE == 'CE' else 'Put Options'})")
print("="*60 + "\n")

if not filtered_ce_masterlist.empty:
    CE_SECURITY_ID = filtered_ce_masterlist.iloc[0]['SEM_SMST_SECURITY_ID']
    print(f"✓ CE Security ID: {CE_SECURITY_ID}")
    print(f"  Trading Symbol: {filtered_ce_masterlist.iloc[0]['SEM_TRADING_SYMBOL']}")
else:
    print("✗ No CE options found")
    CE_SECURITY_ID = None

if not filtered_pe_masterlist.empty:
    PE_SECURITY_ID = filtered_pe_masterlist.iloc[0]['SEM_SMST_SECURITY_ID']
    print(f"✓ PE Security ID: {PE_SECURITY_ID}")
    print(f"  Trading Symbol: {filtered_pe_masterlist.iloc[0]['SEM_TRADING_SYMBOL']}")
else:
    print("✗ No PE options found")
    PE_SECURITY_ID = None

# Choose security ID based on OPTION_TYPE configuration
if OPTION_TYPE == 'CE':
    if CE_SECURITY_ID is None:
        print(f"\n✗ ERROR: No CE options found for strike {NIFTY_PREMIUM} and expiry {EXPIRY_DATE}")
        print("   Please check your strike price and expiry date configuration")
        exit()
    SECURITY_ID = CE_SECURITY_ID
    TRADING_SYMBOL = filtered_ce_masterlist.iloc[0]['SEM_TRADING_SYMBOL']
    print(f"\n→ Using CE (Call) Options")
    print(f"   Security ID: {SECURITY_ID}")
    print(f"   Trading Symbol: {TRADING_SYMBOL}")
elif OPTION_TYPE == 'PE':
    if PE_SECURITY_ID is None:
        print(f"\n✗ ERROR: No PE options found for strike {NIFTY_PREMIUM} and expiry {EXPIRY_DATE}")
        print("   Please check your strike price and expiry date configuration")
        exit()
    SECURITY_ID = PE_SECURITY_ID
    TRADING_SYMBOL = filtered_pe_masterlist.iloc[0]['SEM_TRADING_SYMBOL']
    print(f"\n→ Using PE (Put) Options")
    print(f"   Security ID: {SECURITY_ID}")
    print(f"   Trading Symbol: {TRADING_SYMBOL}")
else:
    print(f"\n✗ Invalid OPTION_TYPE: {OPTION_TYPE}. Please set to 'CE' or 'PE'")
    exit()

print("="*60 + "\n")

# Trading state variables
IS_ACTIVE = False
IS_OPEN_POSITION = False
quantity = 150
buy_price = 0     
stop_loss = 0

# Stop loss settings (simplified - only basic stop loss)

# Phase 1: Wait for activation
print("⏳ PHASE 1: Waiting for Activation")
print(f"   Strategy will activate at second 1 of next minute")
print("-" * 60)

while IS_ACTIVE is False:
    current_time = datetime.datetime.now()
    current_second = current_time.second
    current_minute = current_time.minute
    time_str = current_time.strftime("%H:%M:%S")
    
    # Wait for second 1 (1 second after minute starts)
    if current_second == 1:
        IS_ACTIVE = True
        print(f"\n⏰ [{time_str}] Second 1 of minute {current_minute} - ACTIVATING!")
        print("="*60)
        print("✓ STRATEGY ACTIVATED!")
        print("="*60 + "\n")
        break
    else:
        print(f"⏰ [{time_str}] Waiting for second 1... (current: {current_second})")
        time.sleep(1)

# Phase 2: Buy phase
print("📈 PHASE 2: Buy Phase - Looking for Entry")
print(f"   Stop Loss Mode: Fixed (Buy Price - 2 points)")
print("-" * 60)

while IS_ACTIVE is True and IS_OPEN_POSITION is False:
    current_time = datetime.datetime.now()
    current_second = current_time.second
    time_str = current_time.strftime("%H:%M:%S")
    
    # Exit if we reach the end of the minute (second 59)
    if current_second >= 59:
        print(f"\n⚠️  [{time_str}] End of minute reached, exiting buy phase")
        break
    
    print(f"\n🔍 [{current_time}] Scanning market... (second: {current_second})")
    time.sleep(0.15)  # Rate limit: max 10 Data API calls/sec, 0.15s = 6.67 calls/sec (safe)
    
    try:
        print(f"   → Fetching intraday data for Security ID: {SECURITY_ID}")
        # Get current date for intraday data
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        print(f"   → API Call: SECURITY_ID={SECURITY_ID}, date={current_date}")
        
        # Try the API call with proper string conversion
        try:
            # Convert SECURITY_ID to string to avoid JSON serialization issues
            security_id_str = str(SECURITY_ID)
            print(f"   → Using Security ID as string: {security_id_str}")
            intraday = dhan.intraday_minute_data(security_id_str, dhan.NSE_FNO, "OPTIDX", current_date, current_date, 1)
        except Exception as api_error:
            print(f"   ✗ API Error: {api_error}")
            # Try alternative date format
            alt_date = datetime.datetime.now().strftime("%d-%m-%Y")
            print(f"   → Trying alternative date format: {alt_date}")
            try:
                intraday = dhan.intraday_minute_data(security_id_str, dhan.NSE_FNO, "OPTIDX", alt_date, alt_date, 1)
            except Exception as alt_error:
                print(f"   ✗ Alternative API Error: {alt_error}")
                continue
                
        print(f"   → API Response: {intraday}")
        
        if not intraday or 'data' not in intraday:
            print("   ✗ No data received, retrying...")
            continue
        
        print(f"   ✓ Data received successfully (status: {intraday.get('status', 'unknown')})")
        
        # Debug: Print data structure info
        print(f"   → Data type: {type(intraday.get('data', 'No data key'))}")
        if 'data' in intraday:
            print(f"   → Data length: {len(intraday['data']) if intraday['data'] else 'Empty'}")
        
        # Check if data is valid and not empty
        if not intraday['data'] or len(intraday['data']) == 0:
            print("   ✗ No data available, retrying...")
            continue
            
        try:
            intraday_df = pd.DataFrame(intraday['data'])
            if len(intraday_df) < 2:
                print("   ✗ Insufficient data (need at least 2 candles), retrying...")
                continue
            intraday_df = intraday_df.tail(2)
            print(f"   → Processing last 2 candles ({len(intraday['data'])} total candles available)")
        except Exception as df_error:
            print(f"   ✗ Error creating DataFrame: {df_error}")
            print(f"   → Data structure: {type(intraday['data'])}")
            continue
    except Exception as e:
        print(f"   ✗ Error fetching data: {e}")
        logging.error(f"Error fetching data in buy phase: {e}")
        continue
    # temp_list = []

    # for i in intraday_df['start_Time']:
    #     temp = dhan.convert_to_date_time(i)
    #     temp_list.append(temp)

    # intraday_df['Date'] = temp_list

    previous_closed_candle = intraday_df.iloc[-2]
    current_running_candle = intraday_df.iloc[-1]
    
    # Display market data
    print(f"\n   📊 Market: Prev[{previous_closed_candle['close'].item():.1f}] → Curr[{current_running_candle['close'].item():.1f}] Vol:{current_running_candle['volume'].item():.0f}")
    
    # Buy signal triggered - place order immediately
    print("\n   ✓ BUY SIGNAL TRIGGERED!")
    
    buy_price = current_running_candle['close'].item()
    stop_loss = buy_price - 2  # Stop loss = buy price - 2 points
    
    print(f"\n   💰 Order: {quantity}qty @ ₹{buy_price} | SL: ₹{stop_loss} | Risk: ₹{(buy_price - stop_loss) * quantity}")

    try:
        print(f"\n   📤 Placing BUY order...")
        # order_response = dhan.place_order(
        #     security_id=SECURITY_ID,
        #     exchange_segment=dhan.NSE_FNO,
        #     transaction_type=dhan.BUY,
        #     quantity=quantity,
        #     order_type=dhan.MARKET,
        #     product_type=dhan.INTRA,
        #     price=0)  

        # print(f"   ✓ BUY ORDER PLACED! Response: {order_response}")
        # logging.info(f"BUY {OPTION_TYPE} at {buy_price} - Order Response: {order_response}")

        IS_OPEN_POSITION = True
        print(f"\n✓ {OPTION_TYPE} POSITION OPENED - Moving to Sell Phase\n")
        break
    except Exception as e:
        print(f"\n   ✗ ERROR placing buy order: {e}")
        logging.error(f"Error placing buy order: {e}")
        print("   → Continuing to retry...")
        # Continue trying if order fails

# Phase 3: Sell phase
print("📉 PHASE 3: Sell Phase - Monitoring Position")
print(f"   Position: {quantity} units of {OPTION_TYPE} @ ₹{buy_price}")
print(f"   Stop Loss: ₹{stop_loss}")
print(f"   Stop Loss Mode: Fixed (Buy Price - 2 points)")
print("-" * 60)

while IS_OPEN_POSITION is True and quantity > 0:
    time.sleep(0.15)  # Rate limit: max 10 Data API calls/sec, 0.15s = 6.67 calls/sec (safe)
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    
    try:
        print(f"\n🔍 [{current_time}] Monitoring position...")
        print(f"   → Fetching current market data...")
        # Get current date for intraday data
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        # Convert SECURITY_ID to string to avoid JSON serialization issues
        security_id_str = str(SECURITY_ID)
        intraday = dhan.intraday_minute_data(security_id_str, dhan.NSE_FNO, "OPTIDX", current_date, current_date, 1)
        
        if not intraday or 'data' not in intraday:
            print("   ✗ No data received, retrying...")
            continue
        
        print(f"   ✓ Data received successfully")
        
        # Check if data is valid and not empty
        if not intraday['data'] or len(intraday['data']) == 0:
            print("   ✗ No data available, retrying...")
            continue
            
        try:
            intraday_df = pd.DataFrame(intraday['data'])
            if len(intraday_df) < 2:
                print("   ✗ Insufficient data (need at least 2 candles), retrying...")
                continue
            intraday_df = intraday_df.tail(2)
        except Exception as df_error:
            print(f"   ✗ Error creating DataFrame: {df_error}")
            print(f"   → Data structure: {type(intraday['data'])}")
            continue
        # temp_list = []

        # for i in intraday_df['start_Time']:
        #     temp = dhan.convert_to_date_time(i)
        #     temp_list.append(temp)

        # intraday_df['Date'] = temp_list

        previous_closed_candle = intraday_df.iloc[-2]
        current_running_candle = intraday_df.iloc[-1]
        
        # Display current position status
        current_price = current_running_candle['close'].item()
        pnl = (current_price - buy_price) * quantity
        pnl_percent = ((current_price - buy_price) / buy_price) * 100
        
        print(f"\n   📊 Current Position Status:")
        print(f"      Current Price: ₹{current_price:.2f}")
        print(f"      Entry Price: ₹{buy_price}")
        print(f"      Unrealized P&L: ₹{pnl:.2f} ({pnl_percent:+.2f}%)")
        print(f"      Stop Loss: ₹{stop_loss}")
        print(f"      Distance to SL: ₹{current_price - stop_loss:.2f}")
        
    except Exception as e:
        print(f"   ✗ Error fetching data: {e}")
        logging.error(f"Error fetching data in sell phase: {e}")
        continue

    # Stop loss condition
    if current_running_candle['close'].item() < stop_loss:
        print("\n   ⚠️  STOP LOSS TRIGGERED!")
        print("   " + "-" * 56)
        print(f"      Trigger Price: ₹{current_running_candle['close'].item():.2f}")
        print(f"      Stop Loss Level: ₹{stop_loss}")
        print(f"      Loss: ₹{(current_running_candle['close'].item() - buy_price) * quantity:.2f}")
        
        IS_OPEN_POSITION = False
        
        try:
            print(f"\n   📤 Placing SELL order...")
            # order_response = dhan.place_order(
            #     security_id=SECURITY_ID,
            #     exchange_segment=dhan.NSE_FNO,
            #     transaction_type=dhan.SELL,
            #     quantity=quantity,
            #     order_type=dhan.MARKET,
            #     product_type=dhan.INTRA,
            #     price=0)  
            # print(f"   ✓ SELL ORDER PLACED! Response: {order_response}")
            # logging.info(f"SELL {OPTION_TYPE} SL hit {current_running_candle['close'].item()} - Order Response: {order_response}")
            
            print(f"\n✓ {OPTION_TYPE} POSITION CLOSED - Stop Loss Hit")
        except Exception as e:
            print(f"\n   ✗ ERROR placing sell order: {e}")
            logging.error(f"Error placing sell order (SL): {e}")

print("\n🏁 STRATEGY EXECUTION COMPLETED")
