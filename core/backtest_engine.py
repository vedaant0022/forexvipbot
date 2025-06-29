

import pandas as pd
import os

# Define pip settings per instrument
pip_settings = {
    'XAUUSDm': {'pip_size': 0.01, 'pip_value': 1.0},
    'US500m': {'pip_size': 1.0, 'pip_value': 1.0},
    'USDJPYm': {'pip_size': 0.01, 'pip_value': 9.5},
    'GBPUSDm': {'pip_size': 0.0001, 'pip_value': 10.0},
    'GBPJPYm': {'pip_size': 0.01, 'pip_value': 9.5},
    'USDCHFm': {'pip_size': 0.0001, 'pip_value': 10.0},
    'AUDUSDm': {'pip_size': 0.0001, 'pip_value': 10.0},
    'EURJPYm': {'pip_size': 0.01, 'pip_value': 9.5},
    'BTCUSDm': {'pip_size': 0.01, 'pip_value': 1.0}
}

ACCOUNT_BALANCE = 5000
RISK_PCT = 0.005  # 0.5%

def backtest_signals(signals, symbol, atr_series, rr_ratio=2, stop_atr=1.0, output_path='reports/'):
    trades = []
    pip_info = pip_settings.get(symbol, {'pip_size': 0.0001, 'pip_value': 10.0})
    pip_size = pip_info['pip_size']
    pip_value = pip_info['pip_value']
    risk_amount = ACCOUNT_BALANCE * RISK_PCT  # e.g. $25

    for i, row in signals.iterrows():
        direction = row['direction']
        entry_price = row['close']
        time = row['time']
        atr = atr_series.loc[i] if i in atr_series.index else None
        if pd.isna(atr):
            continue

        # Define SL/TP
        if direction == 'long':
            sl = entry_price - atr * stop_atr
            tp = entry_price + (entry_price - sl) * rr_ratio
        elif direction == 'short':
            sl = entry_price + atr * stop_atr
            tp = entry_price - (sl - entry_price) * rr_ratio
        else:
            continue

        # Calculate SL in pips
        sl_pips = abs(entry_price - sl) / pip_size

        # Calculate lot size: (risk $) / (SL pips * pip value)
        lot_size = risk_amount / (sl_pips * pip_value)
        lot_size = round(lot_size, 2)

        # Simulate result (still simplified)
        result = 'win' if direction == 'long' else 'loss'
        pnl = (tp - entry_price) if result == 'win' else (sl - entry_price)

        trades.append({
            'symbol': symbol,
            'time': time,
            'direction': direction,
            'entry_price': entry_price,
            'stop_loss': sl,
            'take_profit': tp,
            'sl_pips': round(sl_pips, 1),
            'lot_size': lot_size,
            'result': result,
            'PnL': round(pnl, 4),
            'PnL_$': round(pnl / pip_size * pip_value * lot_size, 2)
        })

    df_trades = pd.DataFrame(trades)

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    csv_file = os.path.join(output_path, f"{symbol}_trades.csv")
    df_trades.to_csv(csv_file, index=False)
    print(f"📤 Exported trades to {csv_file}")

    return df_trades
