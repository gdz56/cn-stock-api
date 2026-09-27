"""A-share technical indicators API - Flask app for Render.com."""
from flask import Flask, request, jsonify
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import fetch_quote, fetch_kline, PERIOD_MAP
from indicators import calc_ma, calc_macd, calc_rsi, calc_kdj, calc_boll

app = Flask(__name__)


@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "name": "cn-stock-api",
        "version": "1.0",
        "endpoints": ["/api/quote", "/api/kline", "/api/indicators"],
        "symbol_format": "sh600519, sz000001, bj430047",
    })


@app.route("/api/quote", methods=["GET"])
def quote():
    symbol = request.args.get("symbol", "").strip()
    if not symbol:
        return jsonify({"error": "symbol required, e.g. sh600519"}), 400
    q = fetch_quote(symbol)
    if q:
        return jsonify(q)
    return jsonify({"error": "symbol not found"}), 404


@app.route("/api/kline", methods=["GET"])
def kline():
    symbol = request.args.get("symbol", "").strip()
    if not symbol:
        return jsonify({"error": "symbol required"}), 400
    period = request.args.get("period", "day")
    count = int(request.args.get("count", "120"))
    scale = PERIOD_MAP.get(period, 240)
    data = fetch_kline(symbol, scale, min(count, 500))
    if data:
        return jsonify({"symbol": symbol, "period": period, "count": len(data), "data": data})
    return jsonify({"error": "no data"}), 404


@app.route("/api/indicators", methods=["GET"])
def indicators():
    symbol = request.args.get("symbol", "").strip()
    if not symbol:
        return jsonify({"error": "symbol required"}), 400
    period = request.args.get("period", "day")
    count = int(request.args.get("count", "120"))
    types = request.args.get("types", "ma,macd,rsi,kdj,boll").split(",")
    ma_periods = [int(x) for x in request.args.get("periods", "5,10,20,60").split(",")]
    rsi_period = int(request.args.get("rsi_period", "14"))
    scale = PERIOD_MAP.get(period, 240)
    kline = fetch_kline(symbol, scale, min(count + 60, 500))
    if not kline:
        return jsonify({"error": "no data"}), 404
    closes = [bar["close"] for bar in kline]
    highs = [bar["high"] for bar in kline]
    lows = [bar["low"] for bar in kline]
    trimmed = kline[-count:]
    dates = [bar["date"] for bar in trimmed]
    result = {"symbol": symbol, "period": period, "dates": dates, "indicators": {}}
    for t in types:
        t = t.strip().lower()
        if t == "ma":
            result["indicators"]["ma"] = {}
            for p in ma_periods:
                full = calc_ma(closes, p)
                result["indicators"]["ma"][f"ma{p}"] = full[-count:]
        elif t == "macd":
            full = calc_macd(closes)
            dif = full["dif"][-count:]
            dea = full["dea"][-count:] if len(full["dea"]) >= count else full["dea"][-len(dif):] if dif else []
            hist = full["hist"][-count:]
            result["indicators"]["macd"] = {"dif": dif, "dea": dea, "hist": hist}
        elif t == "rsi":
            full = calc_rsi(closes, rsi_period)
            result["indicators"]["rsi"] = full[-count:]
        elif t == "kdj":
            full = calc_kdj(highs, lows, closes)
            result["indicators"]["kdj"] = {"k": full["k"][-count:], "d": full["d"][-count:], "j": full["j"][-count:]}
        elif t in ("boll", "bollinger"):
            full = calc_boll(closes)
            result["indicators"]["boll"] = {"upper": full["upper"][-count:], "middle": full["middle"][-count:], "lower": full["lower"][-count:]}
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
