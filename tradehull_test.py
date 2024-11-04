from  Dhan_Tradehull import Tradehull
import pdb 
import time
import traceback
import pandas as pd

client_id = "1102249582"
access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzMwNzg2NjIyLCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMjI0OTU4MiJ9.wccDg2vpiW9HCRx3wxyDJn8O9eBnRilGVLAeE66PLl8Im54KOhjDvLKFR3Oh4DbOAXQ8C5KXGaW_tpQUqTBlYg"

tls = Tradehull(client_id, access_token)    


print(tls.get_balance())
#dd = tls.get_ltp("NIFTY 24 OCT 24500 CALL")
ce_name, pe_name, strike = tls.ATM_Strike_Selection('NIFTY','24-10-2024')

print(ce_name, pe_name, strike)