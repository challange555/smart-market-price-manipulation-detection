import pandas as pd
from backend.detector import detect_price_and_volume

df = pd.read_csv("database/market_data/stocks/AAPL.csv")
df["Date"] = pd.to_datetime(df["Date"])

result = detect_price_and_volume(df)

print(result[result["Suspicious"]][
    ["Date", "Close", "Volume", "Price_Change_%"]
])