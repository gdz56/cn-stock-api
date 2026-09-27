"""Sina finance data fetcher - no API key needed, public data."""
import urllib.request
import json
import re
from typing import Optional

SINA_QUOTE_URL = "https://hq.sinajs.cn/list={}"
SINA_KLINE_URL = "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={}&scale={}&ma=no&datalen={}"

HEADERS = {"Referer": "https://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"}


def fetch_quote(symbol: str) -> Optional[dict]:
    """Fetch real-time quote from Sina. symbol format: sh600519, sz000001."""
    url = SINA_QUOTE_URL.format(symbol)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("gbk", errors="replace")
        m = re.search(r'="([^"]*)"', raw)
        if not m or not m.group(1).strip():
            return None
        parts = m.group(1).split(",")
        if len(parts) < 32:
            return None
        return {
            "symbol": symbol,
            "name": parts[0],
            "open": float(parts[1]) if parts[1] else 0,
            "prev_close": float(parts[2]) if parts[2] else 0,
            "last": float(parts[3]) if parts[3] else 0,
            "high": float(parts[4]) if parts[4] else 0,
            "low": float(parts[5]) if parts[5] else 0,
            "volume": float(parts[8]) if parts[8] else 0,
            "amount": float(parts[9]) if parts[9] else 0,
            "date": parts[30],
            "time": parts[31],
            "change": float(parts[3]) - float(parts[2]) if parts[2] and parts[3] else 0,
            "change_pct": round((float(parts[3]) - float(parts[2])) / float(parts[2]) * 100, 2) if parts[2] and parts[3] and float(parts[2]) != 0 else 0,
        }
    except Exception:
        return None


def fetch_kline(symbol: str, scale: int = 240, count: int = 120) -> list:
    """Fetch K-line data. scale: 5/15/30/60 minutes, 240=day. count: number of bars."""
    url = SINA_KLINE_URL.format(symbol, scale, count)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw) if raw.strip() else []
        result = []
        for bar in data:
            result.append({
                "date": bar.get("day", ""),
                "open": float(bar.get("open", 0)),
                "high": float(bar.get("high", 0)),
                "low": float(bar.get("low", 0)),
                "close": float(bar.get("close", 0)),
                "volume": float(bar.get("volume", 0)),
            })
        return result
    except Exception:
        return []


PERIOD_MAP = {"5m": 5, "15m": 15, "30m": 30, "60m": 60, "day": 240, "week": 1680, "month": 7200}
