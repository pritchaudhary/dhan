from dhanhq import dhanhq, marketfeed
import talib
import numpy as np
import pandas as pd
import time
import datetime
import os


# Open the file in read mode
with open("token.txt", "r") as file:
    # Read the entire contents of the file
    token = file.read()

client_id = "1102249582"
access_token = token
dhan = dhanhq(client_id,access_token)
masterlist = None

def get_master_list():
    masterlist = pd.read_csv('https://images.dhan.co/api-data/api-scrip-master.csv', nrows=1)
    masterlist = pd.read_csv('https://images.dhan.co/api-data/api-scrip-master.csv', usecols=masterlist.columns, low_memory=False)


def dd():

    # Print the content
    print(masterlist)

    NIFTY_PREMIMUM = 25800

    filtered_ce_masterlist = masterlist[
        (masterlist.SEM_INSTRUMENT_NAME == 'OPTIDX') &
        (masterlist.SEM_TRADING_SYMBOL.str.startswith('NIFTY')) &
        (masterlist.SEM_EXPIRY_DATE == '2024-11-07 14:30:00') &
        (masterlist.SEM_STRbIKE_PRICE == NIFTY_PREMIMUM) &
        (masterlist.SEM_OPTION_TYPE == 'CE') 
    ]
    filtered_ce_masterlist

#get_master_list()
dd()