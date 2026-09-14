import pandas as pd

def detect_price_and_volume(df):
    # Daily price change
    df["Price_Change_%"] = df["Close"].pct_change() * 100

    # 20-day average volume
    df["Average_Volume"] = df["Volume"].rolling(20).mean()

    # Volume spike
    df["Volume_Spike"] = df["Volume"] > (2 * df["Average_Volume"])

    # Price spike
    df["Price_Spike"] = abs(df["Price_Change_%"]) > 5

    # Final suspicious flag
    df["Suspicious"] = df["Price_Spike"] & df["Volume_Spike"]

    return df