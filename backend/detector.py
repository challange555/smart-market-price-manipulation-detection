import pandas as pd


def detect_price_and_volume(df):

    df = df.copy()

    # Calculate percentage price change
    df["Price_Change_%"] = (
        df["Close"].pct_change() * 100
    )

    # Calculate 20-minute average volume
    df["Average_Volume"] = (
        df["Volume"]
        .rolling(window=20)
        .mean()
    )

    # Calculate volume ratio
    df["Volume_Ratio"] = (
        df["Volume"] /
        df["Average_Volume"]
    )

    # Detect unusual volume
    df["Volume_Spike"] = (
        df["Volume_Ratio"] >= 2
    )

    # Detect unusual price movement
    df["Price_Spike"] = (
        abs(df["Price_Change_%"]) >= 1
    )

    # Final suspicious event
    df["Suspicious"] = (
        df["Price_Spike"] &
        df["Volume_Spike"]
    )

    return df