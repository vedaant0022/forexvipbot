# indicators/structure.py

def detect_double_bottom(df, lookback=20, threshold=0.005):
    bottoms = []
    for i in range(lookback, len(df)):
        low1 = df['low'].iloc[i - lookback]
        low2 = df['low'].iloc[i]
        diff = abs(low1 - low2) / df['low'].iloc[i]
        if diff < threshold and df['close'].iloc[i] > df['close'].iloc[i - 1]:
            bottoms.append(i)
    return df.index.isin(bottoms)

def detect_double_top(df, lookback=20, threshold=0.005):
    tops = []
    for i in range(lookback, len(df)):
        high1 = df['high'].iloc[i - lookback]
        high2 = df['high'].iloc[i]
        diff = abs(high1 - high2) / df['high'].iloc[i]
        if diff < threshold and df['close'].iloc[i] < df['close'].iloc[i - 1]:
            tops.append(i)
    return df.index.isin(tops)
def detect_triple_bottom(df, lookback=30, threshold=0.005):
    bottoms = []
    for i in range(lookback, len(df)):
        low1 = df['low'].iloc[i - lookback]
        low2 = df['low'].iloc[i - lookback // 2]
        low3 = df['low'].iloc[i]
        avg = (low1 + low2 + low3) / 3
        diff1 = abs(low1 - avg) / avg
        diff2 = abs(low2 - avg) / avg
        diff3 = abs(low3 - avg) / avg
        if diff1 < threshold and diff2 < threshold and diff3 < threshold:
            if df['close'].iloc[i] > df['close'].iloc[i - 1]:
                bottoms.append(i)
    return df.index.isin(bottoms)

def detect_triple_top(df, lookback=30, threshold=0.005):
    tops = []
    for i in range(lookback, len(df)):
        high1 = df['high'].iloc[i - lookback]
        high2 = df['high'].iloc[i - lookback // 2]
        high3 = df['high'].iloc[i]
        avg = (high1 + high2 + high3) / 3
        diff1 = abs(high1 - avg) / avg
        diff2 = abs(high2 - avg) / avg
        diff3 = abs(high3 - avg) / avg
        if diff1 < threshold and diff2 < threshold and diff3 < threshold:
            if df['close'].iloc[i] < df['close'].iloc[i - 1]:
                tops.append(i)
    return df.index.isin(tops)
