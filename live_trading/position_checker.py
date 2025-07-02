import MetaTrader5 as mt5

def is_position_open(symbol):
    positions = mt5.positions_get(symbol=symbol)
    return positions is not None and len(positions) > 0
