import numpy as np

def get_support_resistance(df, swing_window=5):
    sr_levels = []
    for i in range(swing_window, len(df) - swing_window):
        is_support = df['low'][i] < df['low'][i - swing_window:i].min() and df['low'][i] < df['low'][i + 1:i + 1 + swing_window].min()
        is_resistance = df['high'][i] > df['high'][i - swing_window:i].max() and df['high'][i] > df['high'][i + 1:i + 1 + swing_window].max()
        if is_support:
            sr_levels.append(('support', df['low'][i]))
        if is_resistance:
            sr_levels.append(('resistance', df['high'][i]))
    return sr_levels


def is_near_level(price, levels, tolerance=0.01):
    for zone_type, level in levels:
        if abs(price - level) / price < tolerance:
            return True
    return False
