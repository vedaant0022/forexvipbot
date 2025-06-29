# from core.mt5_connector import connect_to_mt5, get_data
# from core.signal_engine import generate_signals
# from core.backtest_engine import backtest_signals

# # Step 1: Connect to MetaTrader 5
# if not connect_to_mt5():
#     raise Exception("❌ Could not connect to MetaTrader 5. Please ensure it's open and logged in.")

# # Step 2: Define broker-corrected symbols
# symbols = ['XAUUSDm', 'US500m', 'USDJPYm','GBPUSDm', 'GBPJPYm', 'USDCHFm', 'AUDUSDm', 'EURJPYm','BTCUSDm']

# # Step 3: Loop through each symbol
# for symbol in symbols:
#     print(f"\n🔍 Checking data for {symbol}")

#     d1 = get_data(symbol, "D1", 200)
#     h4 = get_data(symbol, "H4", 500)
#     h1 = get_data(symbol, "H1", 1000)

#     # Skip symbols with missing data
#     if d1.empty or h4.empty or h1.empty:
#         print(f"⚠️ Skipping {symbol} due to missing data")
#         continue

#     print(f"✅ Data loaded for {symbol} | D1: {len(d1)} bars | H4: {len(h4)} bars | H1: {len(h1)} bars")

#     # Step 4: Generate entry signals
#     signals = generate_signals(d1, h4, h1)

#     if signals.empty:
#         print(f"📭 No signals generated for {symbol}")
#         continue

#     print(f"📈 Running backtest for {symbol} with {len(signals)} signals")

#     # Step 5: Run backtest and export trades
#     atr_series = h1['close'].rolling(14).std()  # Simplified ATR
#     trades = backtest_signals(signals, symbol, atr_series)

#     # Step 6: Print summary
#     print(f"📊 {symbol} Results:")
#     print(f"Total Trades: {len(trades)}")
#     print(trades[['time', 'direction', 'result', 'PnL']].tail())


from core.mt5_connector import connect_to_mt5, get_data
from core.signal_engine import generate_signals
from core.backtest_engine import backtest_signals

# Step 1: Connect to MetaTrader 5
if not connect_to_mt5():
    raise Exception("❌ Could not connect to MetaTrader 5. Please ensure it's open and logged in.")

# Step 2: Define broker-corrected symbols
symbols = ['XAUUSDm', 'US500m', 'USDJPYm', 'GBPUSDm', 'GBPJPYm', 'USDCHFm', 'AUDUSDm', 'EURJPYm', 'BTCUSDm']

# Step 3: Loop through each symbol
for symbol in symbols:
    print(f"\n🔍 Checking data for {symbol}")

    d1 = get_data(symbol, "D1", 200)
    h4 = get_data(symbol, "H4", 500)
    h1 = get_data(symbol, "H1", 1000)

    # Skip symbols with missing data
    if d1.empty or h4.empty or h1.empty:
        print(f"⚠️ Skipping {symbol} due to missing data")
        continue

    print(f"✅ Data loaded for {symbol} | D1: {len(d1)} bars | H4: {len(h4)} bars | H1: {len(h1)} bars")

    # Step 4: Generate entry signals
    signals = generate_signals(d1, h4, h1)

    if signals.empty:
        print(f"📭 No signals generated for {symbol}")
        continue

    print(f"📈 Running backtest for {symbol} with {len(signals)} signals")

    # Step 5: Calculate ATR and run backtest
    atr_series = h1['close'].rolling(14).std()
    trades = backtest_signals(signals, h1, symbol, atr_series)  # ✅ Pass h1 as price_data

    # Step 6: Print summary
    print(f"📊 {symbol} Results:")
    print(f"Total Trades: {len(trades)}")
    print(trades[['entry_time', 'exit_time', 'direction', 'result', 'PnL_$']].tail())  # ✅ Updated columns
