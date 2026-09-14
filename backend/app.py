import os
import io
import pandas as pd

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    send_file
)

from backend.data_loader import load_stock_data
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
# GET ALL AVAILABLE STOCKS
# ============================================================

@app.route("/stocks")
def stocks():

    stock_folder = "database/market_data/stocks"

    try:

        files = os.listdir(stock_folder)

        stocks_list = [
            os.path.splitext(file)[0].upper()
            for file in files
            if file.lower().endswith(".csv")
        ]

        stocks_list.sort()

        return jsonify(stocks_list)

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# GENERATE MANIPULATION REASON
# ============================================================

def get_manipulation_reason(row):

    price_change = abs(row["Price_Change_%"])

    volume_ratio = 0

    if (
        pd.notna(row["Average_Volume"])
        and row["Average_Volume"] > 0
    ):
        volume_ratio = (
            row["Volume"] /
            row["Average_Volume"]
        )

    if price_change >= 10 and volume_ratio >= 5:
        return (
            "Extreme price movement + "
            "extreme trading volume"
        )

    elif price_change >= 7 and volume_ratio >= 3:
        return (
            "High price movement + "
            "abnormal trading volume"
        )

    elif price_change >= 5 and volume_ratio >= 2:
        return (
            "Significant price movement + "
            "abnormal trading volume"
        )

    elif price_change >= 5:
        return "Significant price movement"

    elif volume_ratio >= 2:
        return "Abnormal trading volume"

    return "Unusual market activity"


# ============================================================
# PERFORM MARKET ANALYSIS
# ============================================================

def perform_analysis(stock):

    df = load_stock_data(stock)

    result = detect_price_and_volume(df)

    risk_results = result.apply(
        calculate_risk_score,
        axis=1,
        result_type="expand"
    )

    result["Risk_Score"] = risk_results[0]
    result["Risk_Level"] = risk_results[1]

    result["Manipulation_Reason"] = result.apply(
        get_manipulation_reason,
        axis=1
    )

    return result


# ============================================================
# MARKET ANALYSIS
# ============================================================

@app.route("/analyze")
def analyze():

    try:

        stock = request.args.get(
            "stock",
            "AAPL"
        ).upper()

        result = perform_analysis(stock)

        suspicious = result[
            result["Suspicious"]
        ].copy()

        suspicious_data = suspicious[
            [
                "Date",
                "Close",
                "Volume",
                "Price_Change_%",
                "Risk_Score",
                "Risk_Level",
                "Manipulation_Reason"
            ]
        ].copy()

        suspicious_data["Date"] = (
            suspicious_data["Date"]
            .dt.strftime("%Y-%m-%d")
        )

        chart_data = result[
            [
                "Date",
                "Close",
                "Volume",
                "Suspicious"
            ]
        ].copy()

        chart_data["Date"] = (
            chart_data["Date"]
            .dt.strftime("%Y-%m-%d")
        )

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
            if len(suspicious_data) > 0
            else 0
        )

        return jsonify({

            "stock": stock,

            "total_records": total_records,

            "total_suspicious": total_suspicious,

            "high_risk": high_risk,

            "medium_risk": medium_risk,

            "low_risk": low_risk,

            "max_risk": max_risk,

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
# DOWNLOAD ANALYSIS REPORT
# ============================================================

@app.route("/download_report")
def download_report():

    try:

        stock = request.args.get(
            "stock",
            "AAPL"
        ).upper()

        result = perform_analysis(stock)

        report = result[
            result["Suspicious"]
        ].copy()

        report = report[
            [
                "Date",
                "Close",
                "Volume",
                "Price_Change_%",
                "Risk_Score",
                "Risk_Level",
                "Manipulation_Reason"
            ]
        ].copy()

        report.rename(
            columns={
                "Date": "Date",
                "Close": "Close Price",
                "Volume": "Trading Volume",
                "Price_Change_%": "Price Change %",
                "Risk_Score": "Risk Score",
                "Risk_Level": "Risk Level",
                "Manipulation_Reason": "Manipulation Reason"
            },
            inplace=True
        )

        report["Date"] = (
            report["Date"]
            .dt.strftime("%Y-%m-%d")
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
                f"{stock}_manipulation_report.csv"
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