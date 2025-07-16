import time
from datetime import datetime
import os
import pandas as pd
import requests
import MetaTrader5 as mt5
from dotenv import load_dotenv

from core.mt5_connector import connect_to_mt5, get_data
from core.signal_engine import generate_signals
from core.memory_tracker import MemoryTracker

# === Load environment variables ===
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# === Config ===
CHECK_INTERVAL_MINUTES = 15
PRICE_UPDATE_INTERVAL = 15  # Send price update every X minutes

symbols = ['XAUUSDm', 'USDJPYm', 'US500m']
last_price_alert_time = None

# === Telegram Messaging ===
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

# === Send Live Prices to Telegram ===
def send_live_prices():
    message = f"📡 *Live Prices* @ {datetime.utcnow().strftime('%H:%M:%S')} UTC\n"
    for symbol in symbols:
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            message += f"\n*{symbol}*\nBid: `{tick.bid}`\nAsk: `{tick.ask}`"
        else:
            message += f"\n*{symbol}* ❌ No tick data"
    send_telegram_message(message)

# === MT5 Initialization ===
if not connect_to_mt5():
    raise RuntimeError("❌ Could not connect to MetaTrader 5.")

tracker = MemoryTracker()
send_telegram_message("🟢 *Live Engine Started*\nMonitoring markets...")

print("🚀 Live engine initialized.")

# === Live Loop ===
while True:
    now = datetime.utcnow()

    if now.weekday() >= 5:
        print("⏸ Market closed (weekend). Sleeping...")
        time.sleep(60 * 15)
        continue

    # Live price update every PRICE_UPDATE_INTERVAL
    if not last_price_alert_time or (now - last_price_alert_time).seconds > PRICE_UPDATE_INTERVAL * 60:
        send_live_prices()
        last_price_alert_time = now

    for symbol in symbols:
        print(f"\n🔍 Checking {symbol} @ {now.strftime('%Y-%m-%d %H:%M:%S')}")

        d1 = get_data(symbol, "D1", 200)
        h4 = get_data(symbol, "H4", 500)
        h1 = get_data(symbol, "H1", 1000)

        if d1.empty or h4.empty or h1.empty:
            print(f"⚠️ Skipping {symbol}: Missing candle data.")
            continue

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
            print(f"⏩ Already alerted for this signal: {symbol} | {signal_time}")
            continue

        print(f"📡 Sending signal: {symbol} | {direction.upper()} @ {entry_price:.2f}")

        message = (
            f"📊 *NEW SIGNAL ALERT*\n"
            f"🕒 Time: {signal_time}\n"
            f"💹 Symbol: `{symbol}`\n"
            f"📈 Direction: *{direction.upper()}*\n"
            f"💰 Entry: `{entry_price:.2f}`\n"
            f"🎯 TP Level: `{tp_level:.2f}`" if not pd.isna(tp_level) else "🎯 TP Level: `Not defined`"
        )
        send_telegram_message(message)

        # Mark as sent
        tracker.mark_traded(symbol, signal_time, direction)

    print(f"\n⏳ Sleeping for {CHECK_INTERVAL_MINUTES} minutes...\n")
    time.sleep(CHECK_INTERVAL_MINUTES * 60)




# import time
# from datetime import datetime
# import os
# import pandas as pd
# import requests
# import MetaTrader5 as mt5
# from dotenv import load_dotenv

# from core.mt5_connector import connect_to_mt5, get_data
# from core.signal_engine import generate_signals
# from core.memory_tracker import MemoryTracker
# from live_trading.trade_executor import place_trade
# from live_trading.trade_logger import log_trade

# # === Load environment variables ===
# load_dotenv()
# TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
# TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# # === Config ===
# ACCOUNT_BALANCE = 5000
# RISK_PCT = 0.005
# CHECK_INTERVAL_MINUTES = 15
# PRICE_UPDATE_INTERVAL = 15  # Send price update every X minutes

# symbols = ['XAUUSDm', 'USDJPYm', 'US500m']
# last_price_alert_time = None

# pip_settings = {
#     'XAUUSDm': {'pip_size': 0.01, 'pip_value': 1.0},
#     'US500m': {'pip_size': 1.0, 'pip_value': 1.0},
#     'USDJPYm': {'pip_size': 0.01, 'pip_value': 9.5}
# }

# # === Telegram Messaging ===
# def send_telegram_message(message):
#     if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
#         return
#     url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
#     payload = {
#         'chat_id': TELEGRAM_CHAT_ID,
#         'text': message,
#         'parse_mode': 'Markdown'
#     }
#     try:
#         response = requests.post(url, data=payload)
#         if response.status_code == 200:
#             print("✅ Telegram message sent.")
#         else:
#             print(f"❌ Telegram error: {response.text}")
#     except Exception as e:
#         print(f"❌ Telegram exception: {e}")

# # === Send Live Prices to Telegram ===
# def send_live_prices():
#     message = f"📡 *Live Prices* @ {datetime.utcnow().strftime('%H:%M:%S')} UTC\n"
#     for symbol in symbols:
#         tick = mt5.symbol_info_tick(symbol)
#         if tick:
#             message += f"\n*{symbol}*\nBid: `{tick.bid}`\nAsk: `{tick.ask}`"
#         else:
#             message += f"\n*{symbol}* ❌ No tick data"
#     send_telegram_message(message)

# # === MT5 Initialization ===
# if not connect_to_mt5():
#     raise RuntimeError("❌ Could not connect to MetaTrader 5.")

# tracker = MemoryTracker()
# send_telegram_message("🟢 *Live Engine Started*\nMonitoring markets...")

# print("🚀 Live engine initialized.")

# # === Live Loop ===
# while True:
#     now = datetime.utcnow()

#     # Optional: skip weekends
#     if now.weekday() >= 5:
#         print("⏸ Market closed (weekend). Sleeping...")
#         time.sleep(60 * 15)
#         continue

#     # Live price update every PRICE_UPDATE_INTERVAL
#     if not last_price_alert_time or (now - last_price_alert_time).seconds > PRICE_UPDATE_INTERVAL * 60:
#         send_live_prices()
#         last_price_alert_time = now

#     for symbol in symbols:
#         print(f"\n🔍 Checking {symbol} @ {now.strftime('%Y-%m-%d %H:%M:%S')}")

#         d1 = get_data(symbol, "D1", 200)
#         h4 = get_data(symbol, "H4", 500)
#         h1 = get_data(symbol, "H1", 1000)

#         if d1.empty or h4.empty or h1.empty:
#             print(f"⚠️ Skipping {symbol}: Missing candle data.")
#             continue

#         atr_series = h1['close'].rolling(14).std()
#         signals = generate_signals(d1, h4, h1)

#         if signals.empty:
#             print(f"📭 No signals for {symbol}")
#             continue

#         latest = signals.iloc[-1]
#         direction = latest['direction']
#         entry_price = latest['close']
#         signal_time = latest['time']
#         tp_level = latest['tp_level']

#         if tracker.already_traded(symbol, signal_time, direction):
#             print(f"⏩ Already traded this signal: {symbol} | {signal_time}")
#             continue

#         # === ATR-based SL & TP ===
#         atr = atr_series.loc[latest.name]
#         pip_info = pip_settings.get(symbol, {'pip_size': 0.0001, 'pip_value': 10.0})
#         pip_size = pip_info['pip_size']
#         pip_value = pip_info['pip_value']

#         sl = entry_price - atr if direction == 'long' else entry_price + atr
#         tp = tp_level if not pd.isna(tp_level) else (
#             entry_price + 2 * atr if direction == 'long' else entry_price - 2 * atr
#         )

#         sl_pips = abs(entry_price - sl) / pip_size
#         risk_amount = ACCOUNT_BALANCE * RISK_PCT
#         raw_lot = risk_amount / (sl_pips * pip_value)
#         lot = max(int(raw_lot * 100) / 100.0, 0.01)

#         # === SL/TP validation ===
#         symbol_info = mt5.symbol_info(symbol)
#         if not symbol_info:
#             print(f"❌ No symbol info for {symbol}")
#             continue

#         point = symbol_info.point
#         min_stop_distance = symbol_info.trade_stops_level * point
#         tick = mt5.symbol_info_tick(symbol)
#         current_price = tick.ask if direction == 'long' else tick.bid

#         if abs(current_price - sl) < min_stop_distance or abs(tp - current_price) < min_stop_distance:
#             print(f"⚠️ SL/TP too close. Required min: {min_stop_distance:.5f}")
#             send_telegram_message(f"⚠️ *Invalid SL/TP for {symbol}*\nMin SL/TP distance: `{min_stop_distance:.5f}`")
#             continue

#         print(f"📈 {symbol} | {direction.upper()} | Entry: {entry_price:.2f} | SL: {sl:.2f} | TP: {tp:.2f} | Lot: {lot}")

#         # === Place trade ===
#         result, error = place_trade(
#             symbol=symbol,
#             direction='buy' if direction == 'long' else 'sell',
#             lot_size=lot,
#             sl=round(sl, 2),
#             tp=round(tp, 2)
#         )

#         if result:
#             tracker.mark_traded(symbol, signal_time, direction)
#             log_trade({
#                 "symbol": symbol,
#                 "time": str(datetime.now()),
#                 "direction": direction,
#                 "lot": lot,
#                 "entry_price": result.price,
#                 "sl": sl,
#                 "tp": tp,
#                 "ticket": result.order
#             })

#             message = (
#                 f"🚀 *TRADE EXECUTED*\n"
#                 f"📉 Symbol: {symbol}\n"
#                 f"📈 Direction: *{direction.upper()}*\n"
#                 f"💰 Entry: {entry_price:.2f}\n"
#                 f"🛑 SL: {sl:.2f}\n"
#                 f"🎯 TP: {tp:.2f}\n"
#                 f"🪙 Lot Size: {lot}"
#             )
#             send_telegram_message(message)
#         else:
#             send_telegram_message(
#                 f"❌ *FAILED to place trade* for {symbol} @ {entry_price:.2f}\n"
#                 f"Reason: `{error.comment if hasattr(error, 'comment') else error}`\n"
#                 f"Retcode: `{error.retcode if hasattr(error, 'retcode') else 'N/A'}`"
#             )

#     print(f"\n⏳ Sleeping for {CHECK_INTERVAL_MINUTES} minutes...\n")
#     time.sleep(CHECK_INTERVAL_MINUTES * 60)
