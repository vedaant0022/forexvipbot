def ema(df, period=21, col='close'):
    return df[col].ewm(span=period).mean()
