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

# ✅ Crypto symbols (run 24/7)
symbols = ['BTCUSDm']  # Add more if supported: ['BTCUSDm', 'ETHUSDm']

# Pip settings for crypto
pip_settings = {
    'BTCUSDm': {'pip_size': 0.01, 'pip_value': 1.0}
}

# Account and risk setup
ACCOUNT_BALANCE = 5000
RISK_PCT = 0.005  # 0.5% per trade

# === Load last traded timestamps ===
lock_file = 'logs/last_trade_times.json'
if os.path.exists(lock_file):
    with open(lock_file, 'r') as f:
        last_trade_times = json.load(f)
else:
    last_trade_times = {}

for symbol in symbols:
    print(f"\n🔍 Checking signal for {symbol}")

    # === Check if trade is already open ===
    open_positions = mt5.positions_get(symbol=symbol)
    if open_positions and len(open_positions) > 0:
        print(f"⛔ Skipping {symbol}: Position already open.")
        continue

    # === Load price data ===
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

    # ✅ Check if signal was already traded
    # if last_trade_times.get(symbol) == signal_time_str:
    #     print(f"⏩ Skipping {symbol}: Already traded signal at {signal_time_str}")
    #     continue
    if last_trade_times.get(symbol) == signal_time_str:
        open_positions = mt5.positions_get(symbol=symbol)
    if open_positions and len(open_positions) > 0:
        print(f"⏩ Skipping {symbol}: Already traded signal at {signal_time_str}")
        continue

    direction = latest['direction']
    entry_price = latest['close']
    atr = atr_series.loc[latest.name]

    # === SL / TP ===
    sl = round(entry_price - atr, 2) if direction == 'long' else round(entry_price + atr, 2)
    tp = round(entry_price + 2 * atr, 2) if direction == 'long' else round(entry_price - 2 * atr, 2)

    # === Lot Size Calculation ===
    pip_info = pip_settings.get(symbol, {'pip_size': 0.0001, 'pip_value': 10.0})
    pip_size = pip_info['pip_size']
    pip_value = pip_info['pip_value']
    sl_pips = abs(entry_price - sl) / pip_size
    risk_amount = ACCOUNT_BALANCE * RISK_PCT
    raw_lot = risk_amount / (sl_pips * pip_value)
    lot = int(raw_lot * 100) / 100  # Truncate to 2 decimals

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

        # ✅ Record that we traded this signal
        last_trade_times[symbol] = signal_time_str
        os.makedirs('logs', exist_ok=True)
        with open(lock_file, 'w') as f:
            json.dump(last_trade_times, f)
