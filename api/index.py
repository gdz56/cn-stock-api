"""Vercel Serverless entry — A-share technical indicators API."""
from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from data import fetch_quote, fetch_kline, PERIOD_MAP
from indicators import calc_ma, calc_macd, calc_rsi, calc_kdj, calc_boll


def handler(req):
    """Main API handler for Vercel."""
    url = urllib.parse.urlparse(req.get("url", ""))
    path = url.path
    params = urllib.parse.parse_qs(url.query)
    symbol = params.get("symbol", [""])[0].strip()
    if not symbol:
        return {"statusCode": 400, "body": json.dumps({"error": "symbol required, e.g. sh600519"})}

    if path == "/api/quote":
        q = fetch_quote(symbol)
        if q:
            return {"statusCode": 200, "body": json.dumps(q, ensure_ascii=False)}
        return {"statusCode": 404, "body": json.dumps({"error": "symbol not found"})}

    elif path == "/api/kline":
        period = params.get("period", ["day"])[0]
        count = int(params.get("count", ["120"])[0])
        scale = PERIOD_MAP.get(period, 240)
        data = fetch_kline(symbol, scale, min(count, 500))
        if data:
            return {"statusCode": 200, "body": json.dumps({"symbol": symbol, "period": period, "count": len(data), "data": data}, ensure_ascii=False)}
        return {"statusCode": 404, "body": json.dumps({"error": "no data"})}

    elif path == "/api/indicators":
        period = params.get("period", ["day"])[0]
        count = int(params.get("count", ["120"])[0])
        types = params.get("types", ["ma,macd,rsi,kdj,boll"])[0].split(",")
        ma_periods = [int(x) for x in params.get("periods", ["5,10,20,60"])[0].split(",")]
        scale = PERIOD_MAP.get(period, 240)
        kline = fetch_kline(symbol, scale, min(count + 60, 500))
        if not kline:
            return {"statusCode": 404, "body": json.dumps({"error": "no data"})}
        closes = [bar["close"] for bar in kline]
        highs = [bar["high"] for bar in kline]
        lows = [bar["low"] for bar in kline]
        dates = [bar["date"] for bar in kline]
        result = {"symbol": symbol, "period": period, "dates": dates[-count:], "indicators": {}}
        trimmed = kline[-count:]
        t_closes = [bar["close"] for bar in trimmed]
        t_highs = [bar["high"] for bar in trimmed]
        t_lows = [bar["low"] for bar in trimmed]
        for t in types:
            t = t.strip().lower()
            if t == "ma":
                result["indicators"]["ma"] = {}
                for p in ma_periods:
                    full = calc_ma(closes, p)
                    result["indicators"]["ma"][f"ma{p}"] = full[-count:]
            elif t == "macd":
                full = calc_macd(closes)
                result["indicators"]["macd"] = {
                    "dif": full["dif"][-count:],
                    "dea": full["dea"][-count:] if len(full["dea"]) >= count else full["dea"],
                    "hist": full["hist"][-count:],
                }
            elif t == "rsi":
                rsi_period = int(params.get("rsi_period", ["14"])[0])
                full = calc_rsi(closes, rsi_period)
                result["indicators"]["rsi"] = full[-count:]
            elif t == "kdj":
                full = calc_kdj(highs, lows, closes)
                result["indicators"]["kdj"] = {
                    "k": full["k"][-count:],
                    "d": full["d"][-count:],
                    "j": full["j"][-count:],
                }
            elif t in ("boll", "bollinger"):
                full = calc_boll(closes)
                result["indicators"]["boll"] = {
                    "upper": full["upper"][-count:],
                    "middle": full["middle"][-count:],
                    "lower": full["lower"][-count:],
                }
        return {"statusCode": 200, "body": json.dumps(result, ensure_ascii=False)}

    return {"statusCode": 404, "body": json.dumps({"error": f"unknown path: {path}"})}
