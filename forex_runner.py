from core.mt5_connector import connect_to_mt5, get_data
from core.signal_engine import generate_signals
from live_trading.trade_executor import place_trade
from live_trading.trade_logger import log_trade
from datetime import datetime
import MetaTrader5 as mt5
import json
import os

# Connect to MT5
if not connect_to_mt5():
    raise RuntimeError("❌ Could not connect to MetaTrader 5.")

# Exit on weekends
if datetime.utcnow().weekday() >= 5:
    print("📅 Market closed (Weekend). Skipping execution.")
    exit()

symbols = ['XAUUSDm', 'US500m', 'USDJPYm', 'GBPUSDm', 'GBPJPYm', 'USDCHFm', 'AUDUSDm', 'EURJPYm']

pip_settings = {
    'XAUUSDm': {'pip_size': 0.01, 'pip_value': 1.0},
    'US500m': {'pip_size': 1.0, 'pip_value': 1.0},
    'USDJPYm': {'pip_size': 0.01, 'pip_value': 9.5},
    'GBPUSDm': {'pip_size': 0.0001, 'pip_value': 10.0},
    'GBPJPYm': {'pip_size': 0.01, 'pip_value': 9.5},
    'USDCHFm': {'pip_size': 0.0001, 'pip_value': 10.0},
    'AUDUSDm': {'pip_size': 0.0001, 'pip_value': 10.0},
    'EURJPYm': {'pip_size': 0.01, 'pip_value': 9.5},
}

ACCOUNT_BALANCE = 5000
RISK_PCT = 0.005

# Load last trade times
lock_file = 'logs/last_trade_times_forex.json'
if os.path.exists(lock_file):
    with open(lock_file, 'r') as f:
        last_trade_times = json.load(f)
else:
    last_trade_times = {}

for symbol in symbols:
    print(f"\n🔍 Checking signal for {symbol}")

    # ✅ Check if position already open
    open_positions = mt5.positions_get(symbol=symbol)
    if open_positions and len(open_positions) > 0:
        print(f"⛔ Skipping {symbol}: Trade already open.")
        continue

    d1 = get_data(symbol, "D1", 200)
    h4 = get_data(symbol, "H4", 500)
    h1 = get_data(symbol, "H1", 1000)

    if d1.empty or h4.empty or h1.empty:
        print(f"⚠️ Skipping {symbol} due to missing data.")
        continue

    atr_series = h1['close'].rolling(14).std()
    signals = generate_signals(d1, h4, h1)

    if signals.empty:
        print(f"📭 No signals for {symbol}")
        continue

    latest = signals.iloc[-1]
    signal_time_str = str(latest['time'])

    # ✅ Skip if already traded same candle AND position is still open
    if last_trade_times.get(symbol) == signal_time_str:
        print(f"⏩ Skipping {symbol}: Already traded signal at {signal_time_str}")
        continue

    direction = latest['direction']
    entry_price = latest['close']
    atr = atr_series.loc[latest.name]

    sl = round(entry_price - atr, 2) if direction == 'long' else round(entry_price + atr, 2)
    tp = round(entry_price + 2 * atr, 2) if direction == 'long' else round(entry_price - 2 * atr, 2)

    pip_info = pip_settings.get(symbol, {'pip_size': 0.0001, 'pip_value': 10.0})
    pip_size = pip_info['pip_size']
    pip_value = pip_info['pip_value']
    sl_pips = abs(entry_price - sl) / pip_size
    risk_amount = ACCOUNT_BALANCE * RISK_PCT
    raw_lot = risk_amount / (sl_pips * pip_value)
    lot = int(raw_lot * 100) / 100  # Truncate instead of round

    if lot < 0.01:
        print(f"⚠️ Calculated lot size {lot} is too small. Adjusting to minimum 0.01.")
        lot = 0.01

    print(f"📈 {symbol} | {direction.upper()} @ {entry_price} | SL: {sl} | TP: {tp} | Lot: {lot}")

    result = place_trade(
        symbol=symbol,
        direction='buy' if direction == 'long' else 'sell',
        lot_size=lot,
        sl=sl,
        tp=tp
    )

    if result:
        log_trade({
            "symbol": symbol,
            "time": str(datetime.now()),
            "direction": direction,
            "lot": lot,
            "entry_price": result.price,
            "sl": sl,
            "tp": tp,
            "ticket": result.order
        })

        # ✅ Record signal time
        last_trade_times[symbol] = signal_time_str
        os.makedirs('logs', exist_ok=True)
        with open(lock_file, 'w') as f:
            json.dump(last_trade_times, f)


# from core.mt5_connector import connect_to_mt5, get_data
# from core.signal_engine import generate_signals
# from live_trading.trade_executor import place_trade
# from live_trading.trade_logger import log_trade
# from datetime import datetime

# # Connect to MT5
# if not connect_to_mt5():
#     raise RuntimeError("❌ Could not connect to MetaTrader 5.")

# if datetime.utcnow().weekday() >= 5:
#     print("📅 Market closed (Weekend). Skipping execution.")
#     exit()
# # Symbols to trade

# symbols = ['XAUUSDm', 'US500m', 'USDJPYm', 'GBPUSDm', 'GBPJPYm', 'USDCHFm', 'AUDUSDm', 'EURJPYm']



# pip_settings = {
#     'XAUUSDm': {'pip_size': 0.01, 'pip_value': 1.0},
#     'US500m': {'pip_size': 1.0, 'pip_value': 1.0},
#     'USDJPYm': {'pip_size': 0.01, 'pip_value': 9.5},
#     'GBPUSDm': {'pip_size': 0.0001, 'pip_value': 10.0},
#     'GBPJPYm': {'pip_size': 0.01, 'pip_value': 9.5},
#     'USDCHFm': {'pip_size': 0.0001, 'pip_value': 10.0},
#     'AUDUSDm': {'pip_size': 0.0001, 'pip_value': 10.0},
#     'EURJPYm': {'pip_size': 0.01, 'pip_value': 9.5},
# }


# # Account & risk setup
# ACCOUNT_BALANCE = 5000
# RISK_PCT = 0.005  # 0.5% risk

# for symbol in symbols:
#     print(f"🔍 Checking signal for {symbol}")

#     d1 = get_data(symbol, "D1", 200)
#     h4 = get_data(symbol, "H4", 500)
#     h1 = get_data(symbol, "H1", 1000)

#     if d1.empty or h4.empty or h1.empty:
#         print(f"⚠️ Skipping {symbol} due to missing data.")
#         continue

#     atr_series = h1['close'].rolling(14).std()
#     signals = generate_signals(d1, h4, h1)

#     if signals.empty:
#         print(f"📭 No signals for {symbol}")
#         continue

#     latest = signals.iloc[-1]
#     direction = latest['direction']
#     entry_price = latest['close']
#     atr = atr_series.loc[latest.name]

#     sl = round(entry_price - atr, 2) if direction == 'long' else round(entry_price + atr, 2)
#     tp = round(entry_price + 2 * atr, 2) if direction == 'long' else round(entry_price - 2 * atr, 2)

#     # Calculate lot size
#     pip_info = pip_settings.get(symbol, {'pip_size': 0.0001, 'pip_value': 10.0})
#     pip_size = pip_info['pip_size']
#     pip_value = pip_info['pip_value']
#     sl_pips = abs(entry_price - sl) / pip_size
#     risk_amount = ACCOUNT_BALANCE * RISK_PCT
#     lot = round(risk_amount / (sl_pips * pip_value), 2)

#     print(f"📈 {symbol} | {direction.upper()} @ {entry_price} | SL: {sl} | TP: {tp} | Lot: {lot}")

#     result = place_trade(
#         symbol=symbol,
#         direction='buy' if direction == 'long' else 'sell',
#         lot_size=lot,
#         sl=sl,
#         tp=tp
#     )

#     if result:
#         log_trade({
#             "symbol": symbol,
#             "time": str(datetime.now()),
#             "direction": direction,
#             "lot": lot,
#             "entry_price": result.price,
#             "sl": sl,
#             "tp": tp,
#             "ticket": result.order
#         })
