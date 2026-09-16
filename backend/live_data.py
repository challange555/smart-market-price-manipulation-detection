import yfinance as yf
import pandas as pd


def get_live_data(stock):

    ticker = yf.Ticker(stock)

    data = ticker.history(
        period="1d",
        interval="1m",
        auto_adjust=False
    )

    if data.empty:
        return pd.DataFrame()

    data = data.reset_index()

    # Make sure Volume is numeric
    data["Volume"] = pd.to_numeric(
        data["Volume"],
        errors="coerce"
    ).fillna(0)

    # Yahoo may return 0 for the latest unfinished candle.
    # Use the most recent non-zero volume for display/analysis.
    non_zero_volume = data.loc[
        data["Volume"] > 0,
        "Volume"
    ]

    if not non_zero_volume.empty:
        latest_valid_volume = non_zero_volume.iloc[-1]

        if data.iloc[-1]["Volume"] == 0:
            data.loc[data.index[-1], "Volume"] = latest_valid_volume

    return data