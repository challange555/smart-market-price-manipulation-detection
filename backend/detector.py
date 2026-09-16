import pandas as pd


def detect_price_and_volume(df):

    df = df.copy()

    # Make sure Close and Volume are numeric
    df["Close"] = pd.to_numeric(
        df["Close"],
        errors="coerce"
    )

    df["Volume"] = pd.to_numeric(
        df["Volume"],
        errors="coerce"
    )

    # Minute-to-minute price change
    df["Price_Change_%"] = (
        df["Close"].pct_change() * 100
    )

    # Replace zero volume with NaN only for
    # calculating the normal volume baseline
    volume_for_average = (
        df["Volume"].replace(0, float("nan"))
    )

    # Previous 20-minute average volume
    df["Average_Volume"] = (
        volume_for_average
        .rolling(
            window=20,
            min_periods=5
        )
        .mean()
        .shift(1)
    )

    # Volume ratio
    df["Volume_Ratio"] = (
        df["Volume"] /
        df["Average_Volume"]
    )

    # Clean invalid values
    df["Volume_Ratio"] = (
        df["Volume_Ratio"]
        .replace(
            [float("inf"), -float("inf")],
            0
        )
        .fillna(0)
    )

    # Unusual volume
    df["Volume_Spike"] = (
        df["Volume_Ratio"] >= 1.2
    )

    # Unusual price movement
    df["Price_Spike"] = (
        abs(df["Price_Change_%"]) >= 0.03
    )

    # Suspicious activity
    df["Suspicious"] = (
        df["Price_Spike"] &
        df["Volume_Spike"]
    )

    return df