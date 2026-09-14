def calculate_risk_score(row):
    score = 0

    price_change = abs(row["Price_Change_%"])

    # Price movement contribution
    if price_change >= 10:
        score += 50
    elif price_change >= 7:
        score += 40
    elif price_change >= 5:
        score += 30
    elif price_change >= 3:
        score += 15

    # Volume contribution
    if row["Volume_Spike"]:
        volume_ratio = row["Volume"] / row["Average_Volume"]

        if volume_ratio >= 5:
            score += 50
        elif volume_ratio >= 3:
            score += 40
        elif volume_ratio >= 2:
            score += 30
        else:
            score += 15

    # Risk classification
    score = min(score, 100)

    if score >= 70:
        risk_level = "High"
    elif score >= 40:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return score, risk_level