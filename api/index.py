"""Vercel Python Serverless Function - A-share technical indicators API."""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data import fetch_quote, fetch_kline, PERIOD_MAP
from indicators import calc_ma, calc_macd, calc_rsi, calc_kdj, calc_boll


class handler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        symbol = params.get("symbol", [""])[0].strip()

        if not symbol:
            return self._send_json({"error": "symbol required, e.g. sh600519"}, 400)

        if path == "/api/quote":
            q = fetch_quote(symbol)
            if q:
                return self._send_json(q)
            return self._send_json({"error": "symbol not found"}, 404)

        elif path == "/api/kline":
            period = params.get("period", ["day"])[0]
            count = int(params.get("count", ["120"])[0])
            scale = PERIOD_MAP.get(period, 240)
            data = fetch_kline(symbol, scale, min(count, 500))
            if data:
                return self._send_json({"symbol": symbol, "period": period, "count": len(data), "data": data})
            return self._send_json({"error": "no data"}, 404)

        elif path == "/api/indicators":
            period = params.get("period", ["day"])[0]
            count = int(params.get("count", ["120"])[0])
            types = params.get("types", ["ma,macd,rsi,kdj,boll"])[0].split(",")
            ma_periods = [int(x) for x in params.get("periods", ["5,10,20,60"])[0].split(",")]
            scale = PERIOD_MAP.get(period, 240)
            kline = fetch_kline(symbol, scale, min(count + 60, 500))
            if not kline:
                return self._send_json({"error": "no data"}, 404)
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
                    dea = full["dea"][-count:] if len(full["dea"]) >= count else full["dea"][-len(dif):]
                    hist = full["hist"][-count:]
                    result["indicators"]["macd"] = {"dif": dif, "dea": dea, "hist": hist}
                elif t == "rsi":
                    rsi_period = int(params.get("rsi_period", ["14"])[0])
                    full = calc_rsi(closes, rsi_period)
                    result["indicators"]["rsi"] = full[-count:]
                elif t == "kdj":
                    full = calc_kdj(highs, lows, closes)
                    result["indicators"]["kdj"] = {"k": full["k"][-count:], "d": full["d"][-count:], "j": full["j"][-count:]}
                elif t in ("boll", "bollinger"):
                    full = calc_boll(closes)
                    result["indicators"]["boll"] = {"upper": full["upper"][-count:], "middle": full["middle"][-count:], "lower": full["lower"][-count:]}
            return self._send_json(result)

        elif path == "/" or path == "":
            return self._send_json({"name": "cn-stock-api", "version": "1.0", "endpoints": ["/api/quote", "/api/kline", "/api/indicators"], "docs": "symbol format: sh600519, sz000001"})

        return self._send_json({"error": f"unknown path: {path}"}, 404)
