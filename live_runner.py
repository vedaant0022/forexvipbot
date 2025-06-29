# live_runner.py

import time
from datetime import datetime
from core.mt5_connector import connect_to_mt5, get_data
from core.signal_engine import generate_signals
from live_trading.trade_executor import place_trade
from live_trading.trade_logger import log_trade
from core.memory_tracker import MemoryTracker 
from datetime import datetime
import pytz


ist = pytz.timezone('Asia/Kolkata')
now_ist = datetime.now(ist)

weekday = now_ist.weekday()  
hour = now_ist.hour

if weekday == 6 or (weekday == 0 and hour < 5):
    print(f"📅 Market closed — {now_ist.strftime('%A %H:%M')} IST. Algo halted.")
    exit()

# Config
symbols = ['XAUUSDm', 'USDJPYm', 'US500m'] 
CHECK_INTERVAL_MINUTES = 15
ACCOUNT_BALANCE = 5000
RISK_PCT = 0.005
pip_settings = {
    'XAUUSDm': {'pip_size': 0.01, 'pip_value': 1.0},
    'US500m': {'pip_size': 1.0, 'pip_value': 1.0},
    'USDJPYm': {'pip_size': 0.01, 'pip_value': 9.5},
}

# Initialisation
if not connect_to_mt5():
    raise RuntimeError("❌ Could not connect to MetaTrader 5.")

tracker = MemoryTracker()

print("🚀 Live trading engine started...\n")

while True:
    for symbol in symbols:
        print(f"🔍 Checking {symbol} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        d1 = get_data(symbol, "D1", 200)
        h4 = get_data(symbol, "H4", 500)
        h1 = get_data(symbol, "H1", 1000)

        if d1.empty or h4.empty or h1.empty:
            print(f"⚠️ No data for {symbol}, skipping.")
            continue

        atr_series = h1['close'].rolling(14).std()
        signals = generate_signals(d1, h4, h1)

        if signals.empty:
            print(f"📭 No signal for {symbol}")
            continue

        latest = signals.iloc[-1]
        signal_time = latest['time']
        direction = latest['direction']
        entry_price = latest['close']
        atr = atr_series.loc[latest.name]

        # Skip if signal was already traded
        if tracker.already_traded(symbol, signal_time, direction):
            print(f"⏩ Skipping {symbol}: Signal already executed at {signal_time}")
            continue

        # Compute SL/TP
        sl = round(entry_price - atr, 2) if direction == 'long' else round(entry_price + atr, 2)
        tp = round(entry_price + 2 * atr, 2) if direction == 'long' else round(entry_price - 2 * atr, 2)

        # Compute Lot Size
        pip_info = pip_settings[symbol]
        pip_size = pip_info['pip_size']
        pip_value = pip_info['pip_value']
        sl_pips = abs(entry_price - sl) / pip_size
        risk_amount = ACCOUNT_BALANCE * RISK_PCT
        raw_lot = risk_amount / (sl_pips * pip_value)
        lot = max(int(raw_lot * 100) / 100.0, 0.01)

        print(f"📈 {symbol} | {direction.upper()} | Entry: {entry_price} | SL: {sl} | TP: {tp} | Lot: {lot}")

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
            tracker.mark_traded(symbol, signal_time, direction)
        else:
            print(f"❌ Trade failed for {symbol}")

    print(f"🕒 Sleeping for {CHECK_INTERVAL_MINUTES} minutes...\n")
    time.sleep(CHECK_INTERVAL_MINUTES * 60)
