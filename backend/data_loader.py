import pandas as pd


def load_stock_data(stock):
    file_path = f"database/market_data/stocks/{stock}.csv"

    df = pd.read_csv(file_path)

    df["Date"] = pd.to_datetime(df["Date"])

    return df