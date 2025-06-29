# core/mt5_connector.py

import MetaTrader5 as mt5
import pandas as pd

def connect_to_mt5():
    if not mt5.initialize():
        print("❌ MT5 initialization failed:", mt5.last_error())
        return False
    print("✅ Connected to MetaTrader 5")
    return True

def get_data(symbol, timeframe, bars=1000):
    tf_map = {
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1
    }

    rates = mt5.copy_rates_from_pos(symbol, tf_map[timeframe], 0, bars)

    if rates is None or len(rates) == 0:
        print(f"⚠️ No data returned for {symbol} on {timeframe}")
        return pd.DataFrame()

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df
