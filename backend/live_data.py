import yfinance as yf
import pandas as pd


def get_live_data(stock):

    ticker = yf.Ticker(stock)

    data = ticker.history(
        period="1d",
        interval="1m"
    )

    if data.empty:
        return pd.DataFrame()

    data = data.reset_index()

    return data