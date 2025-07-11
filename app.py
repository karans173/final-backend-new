import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
# Setup paths for module imports
sys.path.append(os.path.dirname(os.path.abspath("D:\\Projects\\AI-Driven-Intelligent-Trading-Assistant-for-Real-Time-Market-Analysis-and-Automated-Execution\\ai_agents")))

# Agent imports
from ai_agents.yfinance_agent import fetch_stock_data
from ai_agents.gemini_agent import get_news_summary
from ai_agents.historical_analysis_agent import historical_stock_analysis

sys.path.append(os.path.dirname(os.path.abspath("D:\\Projects\\AI-Driven-Intelligent-Trading-Assistant-for-Real-Time-Market-Analysis-and-Automated-Execution\\AI_Model")))

from AI_Model.sentiment_analysis import analyze_text_file_sentiment, generate_trading_signals
from AI_Model.pipeline import run_stock_prediction, analyze_trend

import pandas as pd

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Allow all for dev
def convert_types(obj):
    if isinstance(obj, dict):
        return {k: convert_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_types(i) for i in obj]
    elif isinstance(obj, (np.generic,)):
        return obj.item()
    else:
        return obj
    
@app.route("/api/stocks", methods=["POST"])
def handle_stock():
    print("📥 Incoming stock request")

    try:
        data = request.get_json()
        stock = data.get("stock")
        symbol = data.get("symbol")
        risk_level = data.get("riskLevel", "moderate")  # conservative | moderate | aggressive

        if not stock or not symbol:
            return jsonify({"error": "Missing stock or symbol"}), 400

        response = {}

        # 1. Fetch latest data
        df = fetch_stock_data(symbol)
        if df is None or df.empty:
            return jsonify({"error": "Failed to fetch stock data"}), 500
        response["latest_data"] = df.tail(5).to_dict(orient="records")

        # 2. Run LSTM model for forecasting
        print("🔮 Running LSTM forecast...")
        model, scaler, historical_df, future_df = run_stock_prediction(symbol)
        trend_analysis = analyze_trend(future_df)
        response["lstm_forecast"] = {
            "trend": trend_analysis["trend"],
            "percent_change": trend_analysis["percent_change"],
            "volatility": trend_analysis["volatility"]
        }

        # 3. Historical ML agent
        print("📊 Running historical ML analysis...")
        historical_result = historical_stock_analysis(symbol)
        response["historical_ml"] = historical_result

        # 4. Run Gemini summary + Sentiment
        print("🧠 Analyzing sentiment from Gemini news summary...")
        news = get_news_summary(stock, symbol)
        sentiment_result = analyze_text_file_sentiment(news)
        if sentiment_result is None or "error" in sentiment_result:
            print("❌ Sentiment analysis failed.")
            print(f"🪵 Reason: {sentiment_result.get('error', 'Unknown error')}")
            print(f"📍 Error Stage: {sentiment_result.get('stage', 'Unknown')}")
            return jsonify({
        "error": sentiment_result.get("error", "Unknown error"),
        "stage": sentiment_result.get("stage", "Unknown")
    }), 500
        response["sentiment_analysis"] = {
            "overall_sentiment": sentiment_result["overall_sentiment"],
            "positive_ratio": sentiment_result["positive_ratio"],
            "avg_sentiment_score": sentiment_result["avg_sentiment_score"]
        }

        # 5. Generate trading signals (uses sentiment + moving averages)
        print("⚙️ Generating trading signals...")
        price_data = {symbol: df}
        signal = generate_trading_signals(price_data, sentiment_result, risk_profile=risk_level)
        response["trading_signal"] = signal[symbol]

        response_clean = convert_types(response)
        print(response_clean)
        return jsonify(response_clean), 200
    
    except Exception as e:
        print("❌ Exception occurred:", e)
        return jsonify({"error": str(e)}), 500


#############################################################################################################
@app.route("/api/live-stocks", methods=["GET"])
def live_stocks():
    try:
        symbols = ["AAPL", "MSFT", "TSLA"]
        live_data = {}

        for symbol in symbols:
            df = fetch_stock_data(symbol, days=7)
            df = df[['Date', 'Close']]
            df = df.groupby('Date').mean().reset_index()
            df.rename(columns={"Close": symbol}, inplace=True)

            if live_data:
                live_data = pd.merge(live_data, df, on="Date", how="outer")
            else:
                live_data = df

        live_data = live_data.fillna(method="ffill").to_dict(orient="records")
        return jsonify(live_data)
    except Exception as e:
        print("❌ Error fetching live stocks:", e)
        return jsonify({"error": str(e)}), 500


##############################################################################################
if __name__ == "__main__":
    print("🚀 Starting AI Trading Assistant backend...")
    app.run(debug=True, use_reloader=False)