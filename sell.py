from dhanhq import marketfeed
import datetime
from dhanhq import dhanhq
import talib
import numpy as np
import pandas as pd
import time





# Add your Dhan Client ID and Access Token
client_id = "1102249582"
access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzI3ODQxMjc3LCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMjI0OTU4MiJ9.PJrWai0MtpqjYT7i6h1HdT3qhCIyL4HoDkhE5A_4T1cBno2lDN0YABgDXJq7IrYC5HFTfpXcLBZ4wg6iX2F4_w"

dhan = dhanhq(client_id,access_token)

SECURITY_ID = "59183"

sl = 0
quantity = 0
instruments = [(2, SECURITY_ID)]  # here 2 for FNO and 51766 is for instrument id

# Type of data subscription
subscription_code = marketfeed.Ticker

def exit_order():
    # Place an order for NSE Futures & Options
    dhan.place_order(security_id=SECURITY_ID,
    exchange_segment=dhan.NSE_FNO,
    transaction_type=dhan.SELL,
    quantity=quantity,
    order_type=dhan.MARKET,
    product_type=dhan.INTRA,
    price=0)  

   



async def on_connect(instance):
    print("Connected to websocket")

async def on_message(instance, message):
    # current_second = datetime.datetime.now().second # this is to check if one minute completed
    ltp =int(message.get('LTP'))
    # if current_second == 1:
    #     get_one_minute_chart(ltp)
    if ltp < sl:
        exit_order()

    print("Received:", message)
    

print("Subscription code :", subscription_code)

feed = marketfeed.DhanFeed(client_id,
    access_token,
    instruments,
    subscription_code,
    on_connect=on_connect,
    on_message=on_message)

feed.run_forever()