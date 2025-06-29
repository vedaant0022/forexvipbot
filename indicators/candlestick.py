# indicators/candlestick.py

def is_bullish_engulfing(df):
    return (
        (df['close'].shift(1) < df['open'].shift(1)) &
        (df['close'] > df['open']) &
        (df['close'] > df['open'].shift(1)) &
        (df['open'] < df['close'].shift(1))
    )

def is_bearish_engulfing(df):
    return (
        (df['close'].shift(1) > df['open'].shift(1)) &
        (df['close'] < df['open']) &
        (df['close'] < df['open'].shift(1)) &
        (df['open'] > df['close'].shift(1))
    )

def is_morning_star(df):
    return (
        (df['close'].shift(2) < df['open'].shift(2)) &
        (df['close'].shift(1) < df['open'].shift(1)) &
        (df['close'] > df['open']) &
        (df['close'] > df['open'].shift(2))
    )

def is_evening_star(df):
    return (
        (df['close'].shift(2) > df['open'].shift(2)) &
        (df['close'].shift(1) > df['open'].shift(1)) &
        (df['close'] < df['open']) &
        (df['close'] < df['open'].shift(2))
    )

def is_hammer(df):
    body = abs(df['close'] - df['open'])
    lower_shadow = df['open'] - df['low']
    return (
        (df['close'] > df['open']) &
        (lower_shadow > 2 * body)
    )

def is_shooting_star(df):
    body = abs(df['close'] - df['open'])
    upper_shadow = df['high'] - df['close']
    return (
        (df['close'] < df['open']) &
        (upper_shadow > 2 * body)
    )

def is_doji(df):
    return abs(df['close'] - df['open']) / (df['high'] - df['low']) < 0.1
