import pandas as pd
import os

# Define pip settings per instrument
pip_settings = {
    'XAUUSDm': {'pip_size': 0.01, 'pip_value': 1.0},
    'US500m': {'pip_size': 1.0, 'pip_value': 1.0},
    'US30m': {'pip_size': 1.0, 'pip_value': 1.0},
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
COOLDOWN_BARS = 10  

def backtest_signals(signals, price_data, symbol, atr_series, rr_ratio=2, stop_atr=1.0, output_path='reports/'):
    trades = []
    pip_info = pip_settings.get(symbol, {'pip_size': 0.0001, 'pip_value': 10.0})
    pip_size = pip_info['pip_size']
    pip_value = pip_info['pip_value']
    risk_amount = ACCOUNT_BALANCE * RISK_PCT

    last_loss_index = {'long': -COOLDOWN_BARS - 1, 'short': -COOLDOWN_BARS - 1}

    for idx, row in signals.iterrows():
        direction = row['direction']
        entry_time = row['time']
        entry_price = row['close']
        atr = atr_series.at[idx] if idx in atr_series.index else None
        if pd.isna(atr):
            continue

        # ✅ Contextual memory filter
        if idx - last_loss_index[direction] <= COOLDOWN_BARS:
            continue

        # Calculate SL/TP
        sl = entry_price - atr * stop_atr if direction == 'long' else entry_price + atr * stop_atr
        tp = entry_price + (entry_price - sl) * rr_ratio if direction == 'long' else entry_price - (sl - entry_price) * rr_ratio

        # SL in pips
        sl_pips = abs(entry_price - sl) / pip_size
        raw_lot = risk_amount / (sl_pips * pip_value)
        lot_size = max(int(raw_lot * 100) / 100.0, 0.01)

        # Candle-by-candle simulation
        post_entry = price_data[price_data['time'] > entry_time].copy()
        if post_entry.empty:
            continue

        result = 'open'
        exit_time = None
        exit_price = None

        for _, bar in post_entry.iterrows():
            if direction == 'long':
                if bar['low'] <= sl:
                    result = 'loss'
                    exit_price = sl
                    exit_time = bar['time']
                    break
                elif bar['high'] >= tp:
                    result = 'win'
                    exit_price = tp
                    exit_time = bar['time']
                    break
            elif direction == 'short':
                if bar['high'] >= sl:
                    result = 'loss'
                    exit_price = sl
                    exit_time = bar['time']
                    break
                elif bar['low'] <= tp:
                    result = 'win'
                    exit_price = tp
                    exit_time = bar['time']
                    break

        if exit_price is None:
            continue

        profit_pips = (exit_price - entry_price) / pip_size
        if direction == 'short':
            profit_pips = -profit_pips
        profit_dollars = profit_pips * pip_value * lot_size

        if result == 'loss':
            last_loss_index[direction] = idx

        trades.append({
            'symbol': symbol,
            'entry_time': entry_time,
            'exit_time': exit_time,
            'direction': direction,
            'entry_price': entry_price,
            'stop_loss': sl,
            'take_profit': tp,
            'exit_price': exit_price,
            'lot_size': lot_size,
            'sl_pips': round(sl_pips, 2),
            'PnL_pips': round(profit_pips, 2),
            'PnL_$': round(profit_dollars, 2),
            'result': result
        })

    df_trades = pd.DataFrame(trades)

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    csv_file = os.path.join(output_path, f"{symbol}_trades.csv")
    df_trades.to_csv(csv_file, index=False)
    print(f"📤 Exported trades to {csv_file}")

    return df_trades

