def calculate_risk_score(row):

    price_change = abs(row["Price_Change_%"])
    volume_ratio = row["Volume_Ratio"]

    # Price score
    if price_change >= 0.50:
        price_score = 50
    elif price_change >= 0.20:
        price_score = 40
    elif price_change >= 0.10:
        price_score = 30
    elif price_change >= 0.05:
        price_score = 20
    elif price_change >= 0.03:
        price_score = 10
    else:
        price_score = 0

    # Volume score
    if volume_ratio >= 3.0:
        volume_score = 50
    elif volume_ratio >= 2.0:
        volume_score = 40
    elif volume_ratio >= 1.5:
        volume_score = 30
    elif volume_ratio >= 1.2:
        volume_score = 20
    else:
        volume_score = 0

    score = price_score + volume_score

    # Risk level
    if score >= 60:
        risk_level = "High"
    elif score >= 30:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return score, risk_level
