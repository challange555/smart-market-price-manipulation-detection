import io
import pandas as pd

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    send_file
)

from backend.live_data import get_live_data
from backend.detector import detect_price_and_volume
from backend.risk_score import calculate_risk_score


app = Flask(
    __name__,
    template_folder="../frontend/templates"
)


# ============================================================
# LOGIN PAGE
# ============================================================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        return render_template("dashboard.html")

    return render_template("login.html")


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# ============================================================
# AVAILABLE STOCKS
# ============================================================

@app.route("/stocks")
def stocks():

    # Stocks supported by Yahoo Finance
    stocks_list = [
        "AAPL",
        "MSFT",
        "TSLA",
        "AMZN",
        "GOOGL",
        "NVDA",
        "NFLX",
        "JPM",
        "UBER",
        "SPOT",
        "META",
        "AMD",
        "INTC",
        "ADBE",
        "PYPL",
        "CRM",
        "ORCL",
        "IBM",
        "QCOM",
        "AVGO"
    ]

    return jsonify(stocks_list)


# ============================================================
# MANIPULATION REASON
# ============================================================

def get_manipulation_reason(row):

    price_change = abs(row["Price_Change_%"])
    volume_ratio = row["Volume_Ratio"]

    if price_change >= 3 and volume_ratio >= 5:

        return (
            "Extreme price movement + "
            "extreme trading volume"
        )

    elif price_change >= 2 and volume_ratio >= 3:

        return (
            "High price movement + "
            "abnormal trading volume"
        )

    elif price_change >= 1 and volume_ratio >= 2:

        return (
            "Significant price movement + "
            "abnormal trading volume"
        )

    elif price_change >= 1:

        return "Significant price movement"

    elif volume_ratio >= 2:

        return "Abnormal trading volume"

    return "Unusual market activity"


# ============================================================
# PERFORM LIVE MARKET ANALYSIS
# ============================================================

def perform_analysis(stock):

    # Get live 1-minute market data
    df = get_live_data(stock)

    if df.empty:
        return pd.DataFrame()

    # Detect suspicious activity
    result = detect_price_and_volume(df)

    # Calculate risk score
    risk_results = result.apply(
        calculate_risk_score,
        axis=1,
        result_type="expand"
    )

    result["Risk_Score"] = risk_results[0]
    result["Risk_Level"] = risk_results[1]

    # Generate manipulation reason
    result["Manipulation_Reason"] = result.apply(
        get_manipulation_reason,
        axis=1
    )

    return result


# ============================================================
# MARKET ANALYSIS API
# ============================================================

@app.route("/analyze")
def analyze():

    try:

        stock = request.args.get(
            "stock",
            "AAPL"
        ).upper()

        result = perform_analysis(stock)

        if result.empty:

            return jsonify({
                "error": "No live market data available."
            }), 404

        suspicious = result[
            result["Suspicious"]
        ].copy()

        # ----------------------------------------------------
        # Suspicious event data
        # ----------------------------------------------------

        suspicious_data = suspicious[
            [
                "Datetime",
                "Close",
                "Volume",
                "Price_Change_%",
                "Volume_Ratio",
                "Risk_Score",
                "Risk_Level",
                "Manipulation_Reason"
            ]
        ].copy()

        suspicious_data["Datetime"] = (
            suspicious_data["Datetime"]
            .astype(str)
        )

        # ----------------------------------------------------
        # Chart data
        # ----------------------------------------------------

        chart_data = result[
            [
                "Datetime",
                "Close",
                "Volume",
                "Suspicious"
            ]
        ].copy()

        chart_data["Datetime"] = (
            chart_data["Datetime"]
            .astype(str)
        )

        # ----------------------------------------------------
        # Summary
        # ----------------------------------------------------

        total_records = len(result)

        total_suspicious = len(
            suspicious_data
        )

        high_risk = int(
            (
                suspicious_data["Risk_Level"]
                == "High"
            ).sum()
        )

        medium_risk = int(
            (
                suspicious_data["Risk_Level"]
                == "Medium"
            ).sum()
        )

        low_risk = int(
            (
                suspicious_data["Risk_Level"]
                == "Low"
            ).sum()
        )

        max_risk = (
            int(
                suspicious_data[
                    "Risk_Score"
                ].max()
            )
            if not suspicious_data.empty
            else 0
        )

        # ----------------------------------------------------
        # Current market information
        # ----------------------------------------------------

        latest = result.iloc[-1]

        current_price = float(
            latest["Close"]
        )

        current_volume = int(
            latest["Volume"]
        )

        current_change = float(
            latest["Price_Change_%"]
        )

        return jsonify({

            "stock": stock,

            "total_records": total_records,

            "total_suspicious": total_suspicious,

            "high_risk": high_risk,

            "medium_risk": medium_risk,

            "low_risk": low_risk,

            "max_risk": max_risk,

            "current_price": current_price,

            "current_volume": current_volume,

            "current_change": current_change,

            "data": suspicious_data.to_dict(
                orient="records"
            ),

            "chart_data": chart_data.to_dict(
                orient="records"
            )

        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# DOWNLOAD LIVE ANALYSIS REPORT
# ============================================================

@app.route("/download_report")
def download_report():

    try:

        stock = request.args.get(
            "stock",
            "AAPL"
        ).upper()

        result = perform_analysis(stock)

        if result.empty:

            return jsonify({
                "error": "No live market data available."
            }), 404

        report = result[
            result["Suspicious"]
        ].copy()

        report = report[
            [
                "Datetime",
                "Close",
                "Volume",
                "Price_Change_%",
                "Volume_Ratio",
                "Risk_Score",
                "Risk_Level",
                "Manipulation_Reason"
            ]
        ].copy()

        report.rename(
            columns={
                "Datetime": "Date & Time",
                "Close": "Close Price",
                "Volume": "Trading Volume",
                "Price_Change_%": "Price Change %",
                "Volume_Ratio": "Volume Ratio",
                "Risk_Score": "Risk Score",
                "Risk_Level": "Risk Level",
                "Manipulation_Reason":
                    "Manipulation Reason"
            },
            inplace=True
        )

        report["Date & Time"] = (
            report["Date & Time"]
            .astype(str)
        )

        output = io.StringIO()

        report.to_csv(
            output,
            index=False
        )

        csv_data = io.BytesIO(
            output.getvalue().encode("utf-8")
        )

        return send_file(
            csv_data,
            mimetype="text/csv",
            as_attachment=True,
            download_name=(
                f"{stock}_live_manipulation_report.csv"
            )
        )

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )