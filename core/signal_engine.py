# # # core/signal_engine.py

# import pandas as pd
# import numpy as np

# def generate_signals(df_d1, df_h4, df_h1):
#     df = df_h1.copy()

#     # === ATR-Based Volatility Filter ===
#     df['atr'] = df['close'].rolling(14).std()
#     df = df[df['atr'] > df['atr'].rolling(50).mean()]

#     # === EMA Trend Filter ===
#     df['ema21'] = df['close'].ewm(span=21).mean()
#     df['trend_up'] = df['close'] > df['ema21']
#     df['trend_down'] = df['close'] < df['ema21']

#     # === Candle Strength Filter ===
#     df['body'] = abs(df['close'] - df['open'])
#     df['range'] = df['high'] - df['low']
#     df['is_strong_body'] = df['body'] > 0.5 * df['range']

#     # === Swing High/Low Detection for MSS/CHoCH ===
#     swing_lookback = 5
#     df['swing_high'] = df['high'][(df['high'] > df['high'].shift(1)) &
#                                   (df['high'] > df['high'].shift(-1)) &
#                                   (df['high'] > df['high'].shift(swing_lookback)) &
#                                   (df['high'] > df['high'].shift(-swing_lookback))]

#     df['swing_low'] = df['low'][(df['low'] < df['low'].shift(1)) &
#                                 (df['low'] < df['low'].shift(-1)) &
#                                 (df['low'] < df['low'].shift(swing_lookback)) &
#                                 (df['low'] < df['low'].shift(-swing_lookback))]

#     df['last_hh'] = df['swing_high'].ffill()
#     df['last_ll'] = df['swing_low'].ffill()

#     df['CHOCH_long'] = df['close'] > df['last_hh'].shift(1)
#     df['CHOCH_short'] = df['close'] < df['last_ll'].shift(1)

#     df['MSS_long'] = df['high'] > df['last_hh'].shift(1)
#     df['MSS_short'] = df['low'] < df['last_ll'].shift(1)

#     # === Fibonacci Zones ===
#     df['fib_high'] = df['high'].rolling(20).max()
#     df['fib_low'] = df['low'].rolling(20).min()
#     df['fib_50'] = df['fib_high'] - (df['fib_high'] - df['fib_low']) * 0.5
#     df['near_fib'] = abs(df['close'] - df['fib_50']) / df['close'] < 0.01

#     # === Support/Resistance Zones from 4H ===
#     sr_levels = []
#     for i in range(5, len(df_h4) - 5):
#         low = df_h4['low']
#         high = df_h4['high']
#         if low[i] < low[i - 5:i].min() and low[i] < low[i + 1:i + 6].min():
#             sr_levels.append(('support', low[i]))
#         if high[i] > high[i - 5:i].max() and high[i] > high[i + 1:i + 6].max():
#             sr_levels.append(('resistance', high[i]))

#     # === Cluster SR Zones ===
#     clustered_levels = []
#     for zone_type, level in sr_levels:
#         if not any(abs(level - l) / l < 0.002 for _, l in clustered_levels):
#             clustered_levels.append((zone_type, level))

#     def is_near_sr(price):
#         return any(abs(price - level) / price < 0.01 for _, level in clustered_levels)

#     df['near_sr'] = df['close'].apply(is_near_sr)

#     # === Time Filter (IST: 9:00 to 18:00 = UTC: 3 to 12) ===
#     df['hour_utc'] = df['time'].dt.hour
#     df = df[(df['hour_utc'] >= 3) & (df['hour_utc'] <= 12)]

#     # === Confluence Score ===
#     df['score_long'] = (
#         df['trend_up'].astype(int) +
#         df['is_strong_body'].astype(int) +
#         df['CHOCH_long'].astype(int) +
#         df['MSS_long'].astype(int) +
#         df['near_fib'].astype(int) +
#         df['near_sr'].astype(int)
#     )

#     df['score_short'] = (
#         df['trend_down'].astype(int) +
#         df['is_strong_body'].astype(int) +
#         df['CHOCH_short'].astype(int) +
#         df['MSS_short'].astype(int) +
#         df['near_fib'].astype(int) +
#         df['near_sr'].astype(int)
#     )

#     df['long_entry'] = df['score_long'] >= 4
#     df['short_entry'] = df['score_short'] >= 4

#     signals = df[df['long_entry'] | df['short_entry']].copy()
#     signals['direction'] = np.where(signals['long_entry'], 'long', 'short')

#     return signals[['time', 'close', 'direction']]

import pandas as pd
import numpy as np

def generate_signals(df_d1, df_h4, df_h1):
    df = df_h1.copy()

    # === ATR-Based Volatility Filter ===
    df['atr'] = df['close'].rolling(14).std()
    df = df[df['atr'] > df['atr'].rolling(50).mean()]

    # === EMA Trend Filter ===
    df['ema21'] = df['close'].ewm(span=21).mean()
    df['trend_up'] = df['close'] > df['ema21']
    df['trend_down'] = df['close'] < df['ema21']

    # === Candle Strength Filter ===
    df['body'] = abs(df['close'] - df['open'])
    df['range'] = df['high'] - df['low']
    df['is_strong_body'] = df['body'] > 0.5 * df['range']

    # === Swing High/Low Detection for MSS/CHoCH ===
    swing_lookback = 5
    df['swing_high'] = df['high'][(df['high'] > df['high'].shift(1)) &
                                  (df['high'] > df['high'].shift(-1)) &
                                  (df['high'] > df['high'].shift(swing_lookback)) &
                                  (df['high'] > df['high'].shift(-swing_lookback))]

    df['swing_low'] = df['low'][(df['low'] < df['low'].shift(1)) &
                                (df['low'] < df['low'].shift(-1)) &
                                (df['low'] < df['low'].shift(swing_lookback)) &
                                (df['low'] < df['low'].shift(-swing_lookback))]

    df['last_hh'] = df['swing_high'].ffill()
    df['last_ll'] = df['swing_low'].ffill()

    df['CHOCH_long'] = df['close'] > df['last_hh'].shift(1)
    df['CHOCH_short'] = df['close'] < df['last_ll'].shift(1)
    df['MSS_long'] = df['high'] > df['last_hh'].shift(1)
    df['MSS_short'] = df['low'] < df['last_ll'].shift(1)

    # === Retest Logic ===
    df['retest_long'] = (abs(df['low'] - df['last_hh']) / df['low'] < 0.003) & df['CHOCH_long']
    df['retest_short'] = (abs(df['high'] - df['last_ll']) / df['high'] < 0.003) & df['CHOCH_short']

    # === Fibonacci Zones ===
    df['fib_high'] = df['high'].rolling(20).max()
    df['fib_low'] = df['low'].rolling(20).min()
    df['fib_50'] = df['fib_high'] - (df['fib_high'] - df['fib_low']) * 0.5
    df['near_fib'] = abs(df['close'] - df['fib_50']) / df['close'] < 0.01

    # === Support/Resistance Zones from 4H ===
    sr_levels = []
    for i in range(5, len(df_h4) - 5):
        low = df_h4['low']
        high = df_h4['high']
        if low[i] < low[i - 5:i].min() and low[i] < low[i + 1:i + 6].min():
            sr_levels.append(('support', low[i]))
        if high[i] > high[i - 5:i].max() and high[i] > high[i + 1:i + 6].max():
            sr_levels.append(('resistance', high[i]))

    # === Cluster SR Zones ===
    clustered_levels = []
    for zone_type, level in sr_levels:
        if not any(abs(level - l) / l < 0.002 for _, l in clustered_levels):
            clustered_levels.append((zone_type, level))

    def get_nearest_sr(price, direction):
        filtered = [l for t, l in clustered_levels if (t == 'resistance' and direction == 'long') or
                                                      (t == 'support' and direction == 'short')]
        if not filtered:
            return np.nan
        diffs = [abs(price - l) for l in filtered]
        return filtered[np.argmin(diffs)]

    def is_near_sr(price):
        return any(abs(price - level) / price < 0.01 for _, level in clustered_levels)

    df['near_sr'] = df['close'].apply(is_near_sr)

    # === Time Filter (IST: 9:00 to 18:00 = UTC: 3 to 12) ===
    df['hour_utc'] = df['time'].dt.hour
    df = df[(df['hour_utc'] >= 3) & (df['hour_utc'] <= 12)]

    # === Confluence Score ===
    df['score_long'] = (
        df['trend_up'].astype(int) +
        df['is_strong_body'].astype(int) +
        df['CHOCH_long'].astype(int) +
        df['MSS_long'].astype(int) +
        df['retest_long'].astype(int) +
        df['near_fib'].astype(int) +
        df['near_sr'].astype(int)
    )

    df['score_short'] = (
        df['trend_down'].astype(int) +
        df['is_strong_body'].astype(int) +
        df['CHOCH_short'].astype(int) +
        df['MSS_short'].astype(int) +
        df['retest_short'].astype(int) +
        df['near_fib'].astype(int) +
        df['near_sr'].astype(int)
    )

    df['long_entry'] = df['score_long'] >= 5
    df['short_entry'] = df['score_short'] >= 5

    signals = df[df['long_entry'] | df['short_entry']].copy()
    signals['direction'] = np.where(signals['long_entry'], 'long', 'short')
    signals['tp_level'] = signals.apply(lambda x: get_nearest_sr(x['close'], x['direction']), axis=1)

    return signals[['time', 'close', 'direction', 'tp_level']]
