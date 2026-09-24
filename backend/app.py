import io
import os
import pandas as pd

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    send_file,
    redirect,
    url_for,
    session
)

from backend.live_data import get_live_data
from backend.detector import detect_price_and_volume
from backend.risk_score import calculate_risk_score


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(
    __name__,
    template_folder="../frontend/templates"
)

# Secret key for login sessions
app.secret_key = "smart-market-surveillance-secret-key"


# ============================================================
# LOGIN REQUIRED FUNCTION
# ============================================================

def login_required():

    if not session.get("logged_in"):
        return False

    return True


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    return render_template("home.html")


# ============================================================
# LOGIN PAGE
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    # Already logged in
    if session.get("logged_in"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        # ----------------------------------------------------
        # LOGIN DETAILS
        # ----------------------------------------------------

        if username == "admin" and password == "admin123":

            session["logged_in"] = True
            session["username"] = username

            return redirect(
                url_for("dashboard")
            )

        return render_template(
            "login.html",
            error="Invalid username or password."
        )

    return render_template("login.html")


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# ============================================================
# MARKET ANALYSIS PAGE
# ============================================================

@app.route("/dashboard")
@app.route("/analysis")
def dashboard():

    if not login_required():
        return redirect(
            url_for("login")
        )

    return render_template(
        "dashboard.html"
    )


# ============================================================
# RISK DETECTION PAGE
# ============================================================

@app.route("/risk")
def risk():

    if not login_required():
        return redirect(
            url_for("login")
        )

    return render_template(
        "risk.html"
    )


# ============================================================
# REPORTS PAGE
# ============================================================

@app.route("/reports")
def reports():

    if not login_required():
        return redirect(
            url_for("login")
        )

    return render_template(
        "reports.html"
    )


# ============================================================
# ABOUT SYSTEM PAGE
# ============================================================

@app.route("/about")
def about():

    if not login_required():
        return redirect(
            url_for("login")
        )

    return render_template(
        "about.html"
    )


# ============================================================
# PROJECT INFORMATION PAGE
# ============================================================

@app.route("/project")
def project():

    if not login_required():
        return redirect(
            url_for("login")
        )

    return render_template(
        "project.html"
    )


# ============================================================
# AVAILABLE STOCKS
# ============================================================

@app.route("/stocks")
def stocks():

    if not login_required():
        return jsonify({
            "error": "Login required."
        }), 401

    stocks_folder = os.path.join(
        os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        ),
        "database",
        "market_data",
        "stocks"
    )

    if not os.path.exists(stocks_folder):
        return jsonify([])

    stocks_list = []

    for file in os.listdir(stocks_folder):

        if file.lower().endswith(".csv"):

            ticker = os.path.splitext(
                file
            )[0].upper()

            stocks_list.append(ticker)

    stocks_list = sorted(
        set(stocks_list)
    )

    return jsonify(stocks_list)


# ============================================================
# MANIPULATION REASON
# ============================================================

def get_manipulation_reason(row):

    price_change = abs(
        row["Price_Change_%"]
    )

    volume_ratio = row[
        "Volume_Ratio"
    ]

    if (
        price_change >= 0.50
        and volume_ratio >= 3.0
    ):

        return (
            "Extreme price movement + "
            "extreme trading volume"
        )

    elif (
        price_change >= 0.20
        and volume_ratio >= 2.0
    ):

        return (
            "High price movement + "
            "abnormal trading volume"
        )

    elif (
        price_change >= 0.10
        and volume_ratio >= 1.5
    ):

        return (
            "Significant price movement + "
            "increased trading volume"
        )

    elif (
        price_change >= 0.03
        and volume_ratio >= 1.2
    ):

        return (
            "Unusual price movement + "
            "volume spike"
        )

    elif price_change >= 0.03:

        return "Unusual price movement"

    elif volume_ratio >= 1.2:

        return "Unusual trading volume"

    return "Unusual market activity"


# ============================================================
# PERFORM MARKET ANALYSIS
# ============================================================

def perform_analysis(stock):

    df = get_live_data(stock)

    if df.empty:
        return pd.DataFrame()

    result = detect_price_and_volume(df)

    risk_results = result.apply(
        calculate_risk_score,
        axis=1,
        result_type="expand"
    )

    result["Risk_Score"] = (
        risk_results[0]
    )

    result["Risk_Level"] = (
        risk_results[1]
    )

    result["Manipulation_Reason"] = (
        result.apply(
            get_manipulation_reason,
            axis=1
        )
    )

    return result


# ============================================================
# MARKET ANALYSIS API
# ============================================================

@app.route("/analyze")
def analyze():

    if not login_required():
        return jsonify({
            "error": "Login required."
        }), 401

    try:

        stock = request.args.get(
            "stock",
            "AAPL"
        ).upper().strip()

        result = perform_analysis(
            stock
        )

        if result.empty:

            return jsonify({
                "error":
                    "No market data available."
            }), 404

        suspicious = result[
            result["Suspicious"] == True
        ].copy()

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

        suspicious_data[
            "Datetime"
        ] = suspicious_data[
            "Datetime"
        ].astype(str)

        chart_data = result[
            [
                "Datetime",
                "Close",
                "Volume",
                "Suspicious"
            ]
        ].copy()

        chart_data[
            "Datetime"
        ] = chart_data[
            "Datetime"
        ].astype(str)

        total_records = len(
            result
        )

        total_suspicious = len(
            suspicious_data
        )

        high_risk = int(
            (
                result["Risk_Level"]
                == "High"
            ).sum()
        )

        medium_risk = int(
            (
                result["Risk_Level"]
                == "Medium"
            ).sum()
        )

        low_risk = int(
            (
                result["Risk_Level"]
                == "Low"
            ).sum()
        )

        max_risk = int(
            result["Risk_Score"].max()
        )

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

            "total_records":
                total_records,

            "total_suspicious":
                total_suspicious,

            "high_risk":
                high_risk,

            "medium_risk":
                medium_risk,

            "low_risk":
                low_risk,

            "max_risk":
                max_risk,

            "current_price":
                current_price,

            "current_volume":
                current_volume,

            "current_change":
                current_change,

            "data":
                suspicious_data.to_dict(
                    orient="records"
                ),

            "chart_data":
                chart_data.to_dict(
                    orient="records"
                )
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# DOWNLOAD REPORT
# ============================================================

@app.route("/download_report")
def download_report():

    if not login_required():
        return jsonify({
            "error": "Login required."
        }), 401

    try:

        stock = request.args.get(
            "stock",
            "AAPL"
        ).upper().strip()

        result = perform_analysis(
            stock
        )

        if result.empty:

            return jsonify({
                "error":
                    "No market data available."
            }), 404

        report = result[
            result["Suspicious"] == True
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
        ]

        report.rename(
            columns={

                "Datetime":
                    "Date & Time",

                "Close":
                    "Close Price",

                "Volume":
                    "Trading Volume",

                "Price_Change_%":
                    "Price Change %",

                "Volume_Ratio":
                    "Volume Ratio",

                "Risk_Score":
                    "Risk Score",

                "Risk_Level":
                    "Risk Level",

                "Manipulation_Reason":
                    "Manipulation Reason"

            },
            inplace=True
        )

        report[
            "Date & Time"
        ] = report[
            "Date & Time"
        ].astype(str)

        output = io.StringIO()

        report.to_csv(
            output,
            index=False
        )

        csv_data = io.BytesIO(
            output
            .getvalue()
            .encode("utf-8")
        )

        return send_file(

            csv_data,

            mimetype="text/csv",

            as_attachment=True,

            download_name=(
                f"{stock}_"
                "live_manipulation_report.csv"
            )
        )

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "home.html"
    ), 404


@app.errorhandler(500)
def internal_server_error(error):

    return jsonify({
        "error":
            "Internal server error."
    }), 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )