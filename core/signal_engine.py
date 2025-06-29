# core/signal_engine.py

import pandas as pd
import numpy as np
from indicators.ema import ema
from indicators.candlestick import is_bullish_engulfing, is_bearish_engulfing
from indicators.structure import detect_double_bottom, detect_double_top
from indicators.structure import (
    detect_double_bottom, detect_double_top,
    detect_triple_bottom, detect_triple_top
)
from indicators.zones import get_support_resistance, is_near_level


def detect_structure(df, swing_lookback=5):
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
    return df


def detect_mss_choch(df):
    df['MSS_long'] = (df['high'] > df['last_hh'].shift(1))
    df['CHOCH_short'] = (df['low'] < df['last_ll'].shift(1))

    df['MSS_short'] = (df['low'] < df['last_ll'].shift(1))
    df['CHOCH_long'] = (df['high'] > df['last_hh'].shift(1))

    return df


def fibonacci_levels(df):
    df['swing_high'] = df['high'].rolling(20).max()
    df['swing_low'] = df['low'].rolling(20).min()

    df['fib_30'] = df['swing_high'] - (df['swing_high'] - df['swing_low']) * 0.3
    df['fib_50'] = df['swing_high'] - (df['swing_high'] - df['swing_low']) * 0.5
    df['fib_618'] = df['swing_high'] - (df['swing_high'] - df['swing_low']) * 0.618

    return df


def generate_signals(df_d1, df_h4, df_h1):
    df = df_h1.copy()

    # === Trend Filter ===
    df['ema21'] = ema(df, 21)
    df['trend_up'] = df['close'] > df['ema21']
    df['trend_down'] = df['close'] < df['ema21']

    # === Candlestick Confirmations ===
    df['bull_engulf'] = is_bullish_engulfing(df)
    df['bear_engulf'] = is_bearish_engulfing(df)

    # === Structure & MSS/CHOCH ===
    df = detect_structure(df)
    df = detect_mss_choch(df)

    # === Fib Zones ===
    df = fibonacci_levels(df)

    df['near_fib'] = (
        (df['close'] >= df['fib_30'] * 0.998) & (df['close'] <= df['fib_30'] * 1.002) |
        (df['close'] >= df['fib_50'] * 0.998) & (df['close'] <= df['fib_50'] * 1.002) |
        (df['close'] >= df['fib_618'] * 0.998) & (df['close'] <= df['fib_618'] * 1.002)
    )
    
    # === Chart Patterns ===
    df['double_bottom'] = detect_double_bottom(df)
    df['double_top'] = detect_double_top(df)
    df['triple_bottom'] = detect_triple_bottom(df)
    df['triple_top'] = detect_triple_top(df)
    
    # === Support/Resistance Zones from 4H ===
    sr_levels = get_support_resistance(df_h4)

    # Map if current price is near a zone
    df['near_sr'] = df['close'].apply(lambda price: is_near_level(price, sr_levels, tolerance=0.01))

    # === Final Confluence Conditions ===
    df['long_entry'] = (
        df['trend_up'] &
        (df['bull_engulf'] | df['double_bottom'] | df['triple_bottom']) &
        df['MSS_long'] &
        df['near_fib'] &
        df['near_sr']  
    )

    df['short_entry'] = (
        df['trend_down'] &
        (df['bear_engulf'] | df['double_top'] | df['triple_top']) &
        df['MSS_short'] &
        df['near_fib'] &
        df['near_sr'] 
    )
    # === Combine and Return Entry Points ===
    signals = df[(df['long_entry'] | df['short_entry'])].copy()
    signals['direction'] = np.where(signals['long_entry'], 'long', 'short')
    return signals[['time', 'close', 'direction']]
