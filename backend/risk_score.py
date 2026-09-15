def calculate_risk_score(row):

    score = 0

    price_change = abs(row["Price_Change_%"])
    volume_ratio = row["Volume_Ratio"]

    # Price movement
    if price_change >= 3:
        score += 50
    elif price_change >= 2:
        score += 40
    elif price_change >= 1:
        score += 30

    # Volume movement
    if volume_ratio >= 5:
        score += 50
    elif volume_ratio >= 3:
        score += 40
    elif volume_ratio >= 2:
        score += 30

    score = min(score, 100)

    if score >= 70:
        risk_level = "High"
    elif score >= 40:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return score, risk_level