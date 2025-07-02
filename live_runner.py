import time
from datetime import datetime
import pytz
import os
from dotenv import load_dotenv
import pandas as pd
from core.mt5_connector import connect_to_mt5, get_data
from core.signal_engine import generate_signals
from core.memory_tracker import MemoryTracker
from live_trading.trade_executor import place_trade
from live_trading.trade_logger import log_trade
import requests

# === Load .env ===
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_message(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("✅ Telegram message sent.")
        else:
            print(f"❌ Telegram error: {response.text}")
    except Exception as e:
        print(f"❌ Telegram exception: {e}")

# === Connect to MT5 ===
if not connect_to_mt5():
    raise RuntimeError("❌ Could not connect to MetaTrader 5.")

# === Symbols and config ===
symbols = ['XAUUSDm', 'USDJPYm', 'US500m']
ACCOUNT_BALANCE = 5000
RISK_PCT = 0.005
CHECK_INTERVAL_MINUTES = 15

pip_settings = {
    'XAUUSDm': {'pip_size': 0.01, 'pip_value': 1.0},
    'US500m': {'pip_size': 1.0, 'pip_value': 1.0},
    'USDJPYm': {'pip_size': 0.01, 'pip_value': 9.5}
}

tracker = MemoryTracker()
send_telegram_message("🤖 *Live Server Started*\nMonitoring Forex signals...")

print("🚀 Live trading engine started...\n")

while True:
    now = datetime.utcnow()
    if now.weekday() >= 5:  # Saturday or Sunday
        print("⏸ Market is closed (weekend). Sleeping...")
        time.sleep(60 * 15)
        continue

    for symbol in symbols:
        print(f"\n🔍 Checking {symbol} at {now.strftime('%Y-%m-%d %H:%M:%S')}")

        d1 = get_data(symbol, "D1", 200)
        h4 = get_data(symbol, "H4", 500)
        h1 = get_data(symbol, "H1", 1000)

        if d1.empty or h4.empty or h1.empty:
            print(f"⚠️ Skipping {symbol}: Missing data.")
            continue

        atr_series = h1['close'].rolling(14).std()
        signals = generate_signals(d1, h4, h1)

        if signals.empty:
            print(f"📭 No signals for {symbol}")
            continue

        latest = signals.iloc[-1]
        direction = latest['direction']
        entry_price = latest['close']
        signal_time = latest['time']
        tp_level = latest['tp_level']

        if tracker.already_traded(symbol, signal_time, direction):
            print(f"⏩ Skipping {symbol}: Already traded signal at {signal_time}")
            continue

        atr = atr_series.loc[latest.name]
        pip_info = pip_settings.get(symbol, {'pip_size': 0.0001, 'pip_value': 10.0})
        pip_size = pip_info['pip_size']
        pip_value = pip_info['pip_value']

        sl = entry_price - atr if direction == 'long' else entry_price + atr
        tp = tp_level if not pd.isna(tp_level) else (entry_price + 2 * atr if direction == 'long' else entry_price - 2 * atr)

        sl_pips = abs(entry_price - sl) / pip_size
        risk_amount = ACCOUNT_BALANCE * RISK_PCT
        raw_lot = risk_amount / (sl_pips * pip_value)
        lot = max(int(raw_lot * 100) / 100.0, 0.01)

        print(f"📈 {symbol} | {direction.upper()} | Entry: {entry_price:.2f} | SL: {sl:.2f} | TP: {tp:.2f} | Lot: {lot}")

        result = place_trade(
            symbol=symbol,
            direction='buy' if direction == 'long' else 'sell',
            lot_size=lot,
            sl=round(sl, 2),
            tp=round(tp, 2)
        )

        if result:
            tracker.mark_traded(symbol, signal_time, direction)
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

            msg = (
                f"🚀 *TRADE PLACED*\n"
                f"📉 Symbol: {symbol}\n"
                f"📈 Direction: *{direction.upper()}*\n"
                f"💰 Entry: {entry_price:.2f}\n"
                f"🛑 SL: {sl:.2f}\n"
                f"🎯 TP: {tp:.2f}\n"
                f"🪙 Lot Size: {lot}"
            )
            send_telegram_message(msg)
        else:
            send_telegram_message(f"⚠️ *FAILED to place trade for {symbol}* at {entry_price:.2f}")

    print(f"\n🕒 Sleeping for {CHECK_INTERVAL_MINUTES} minutes...\n")
    time.sleep(CHECK_INTERVAL_MINUTES * 60)


# import time
# import os
# import pandas as pd
# import requests
# import pytz
# from datetime import datetime
# from dotenv import load_dotenv

# from core.mt5_connector import get_data, connect_to_mt5
# from core.signal_engine import generate_signals
# from core.memory_tracker import MemoryTracker

# # === Load environment variables ===
# load_dotenv()

# TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
# TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
#     raise ValueError("❌ TELEGRAM_TOKEN or TELEGRAM_CHAT_ID not set in .env")

# def send_telegram_message(message):
#     if not message.strip():
#         print("❌ Message is empty. Skipping.")
#         return
#     url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
#     payload = {
#         'chat_id': TELEGRAM_CHAT_ID,
#         'text': message,
#         'parse_mode': 'Markdown'
#     }
#     response = requests.post(url, data=payload)
#     if response.status_code != 200:
#         print(f"❌ Failed to send Telegram message: {response.text}")
#     else:
#         print("✅ Telegram message sent.")

# def is_market_open():
#     ist = pytz.timezone("Asia/Kolkata")
#     now = datetime.now(ist)
#     weekday = now.weekday()
#     hour = now.hour
#     return not (weekday == 6 or (weekday == 0 and hour < 5))

# # === Init ===
# symbols = ['XAUUSDm', 'USDJPYm', 'US500m']
# tracker = MemoryTracker()

# if not connect_to_mt5():
#     raise RuntimeError("❌ Could not connect to MetaTrader 5.")

# print("🚀 Continuous Live Signal Engine Running...\n")
# send_telegram_message("🤖 *Vedaant's Continuous Signal Bot is Live!*\nMonitoring charts in real time...")

# # === Main Loop ===
# while True:
#     if not is_market_open():
#         print("⏸ Market closed — waiting...")
#         time.sleep(30)
#         continue

#     for symbol in symbols:
#         print(f"🔍 Checking {symbol} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

#         d1 = get_data(symbol, "D1", 200)
#         h4 = get_data(symbol, "H4", 500)
#         h1 = get_data(symbol, "H1", 1000)

#         if d1.empty or h4.empty or h1.empty:
#             print(f"⚠️ No data for {symbol}, skipping.")
#             continue

#         signals = generate_signals(d1, h4, h1)
#         if signals.empty:
#             continue

#         latest = signals.iloc[-1]
#         signal_time = latest['time']
#         direction = latest['direction']
#         entry_price = latest['close']
#         tp_level = latest.get('tp_level', 'N/A')

#         if tracker.already_traded(symbol, signal_time, direction):
#             continue

#         msg = (
#             f"📢 *{symbol} {direction.upper()} SIGNAL*\n"
#             f"🕒 Time: {signal_time}\n"
#             f"💰 Entry: {entry_price}\n"
#             f"🎯 TP Level: {tp_level}"
#         )

#         send_telegram_message(msg)
#         tracker.mark_traded(symbol, signal_time, direction)

#     time.sleep(3)  



