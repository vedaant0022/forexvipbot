import MetaTrader5 as mt5

def place_trade(symbol, direction, lot_size, sl, tp, magic=20250701, comment="CryptoBot", deviation=30):
    if not mt5.initialize():
        raise RuntimeError("❌ Could not connect to MetaTrader 5")

    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"⚠️ Symbol {symbol} not found.")
        return None

    if not symbol_info.visible:
        mt5.symbol_select(symbol, True)

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(f"⚠️ No live tick data for {symbol}")
        return None

    price = tick.ask if direction == 'buy' else tick.bid
    order_type = mt5.ORDER_TYPE_BUY if direction == 'buy' else mt5.ORDER_TYPE_SELL

    print(f"🧪 Attempting {direction.upper()} | Price: {price} | SL: {sl} | TP: {tp} | Lot: {lot_size}")

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": deviation,
        "magic": magic,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC 
    }

    result = mt5.order_send(request)
    mt5.shutdown()

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"❌ Trade failed for {symbol}: {result.retcode}")
        print(f"🛠 Full Error: {result}")
        return None

    print(f"✅ Trade placed: {symbol} | {direction.upper()} | Lot: {lot_size} | Entry: {result.price}")
    return result
