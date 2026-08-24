"""Free portfolio price refresh using yfinance – no broker API needed."""
from datetime import datetime, timezone
from typing import Optional
import yfinance as yf


def _yf_symbol(symbol: str, exchange: str) -> str:
    if exchange.upper() == "BSE":
        return f"{symbol}.BO"
    return f"{symbol}.NS"   # NSE default


def lookup_stock(symbol: str, exchange: str = "NSE") -> dict | None:
    """Fetch current price + metadata for a symbol. Returns None if not found."""
    ticker = yf.Ticker(_yf_symbol(symbol, exchange))
    info = ticker.info or {}
    hist = ticker.history(period="2d")
    if hist.empty:
        return None
    last = float(hist["Close"].iloc[-1])
    prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else last
    return {
        "symbol": symbol.upper(),
        "exchange": exchange.upper(),
        "company_name": info.get("longName") or info.get("shortName") or symbol.upper(),
        "sector": info.get("sector") or "Unknown",
        "industry": info.get("industry") or "Unknown",
        "last_price": round(last, 2),
        "close_price": round(prev, 2),
        "day_change": round(last - prev, 2),
        "day_change_pct": round((last - prev) / prev * 100, 2) if prev else 0.0,
    }


def refresh_prices(holdings: list[dict]) -> list[dict]:
    """Bulk-refresh last_price for a list of {symbol, exchange} dicts using yfinance."""
    if not holdings:
        return []
    symbols = [_yf_symbol(h["tradingsymbol"], h.get("exchange", "NSE")) for h in holdings]
    try:
        import pandas as pd
        raw = yf.download(symbols, period="2d", interval="1d", progress=False, group_by="ticker")
    except Exception:
        return holdings

    results = []
    for h in holdings:
        yf_sym = _yf_symbol(h["tradingsymbol"], h.get("exchange", "NSE"))
        try:
            if len(symbols) == 1:
                df = raw
            else:
                df = raw[yf_sym]
            last = float(df["Close"].iloc[-1])
            prev = float(df["Close"].iloc[-2]) if len(df) > 1 else last
            h["last_price"] = round(last, 2)
            h["close_price"] = round(prev, 2)
            h["day_change"] = round(last - prev, 2)
            h["day_change_pct"] = round((last - prev) / prev * 100, 2) if prev else 0.0
        except Exception:
            pass
        results.append(h)
    return results
        except Exception:
            return []


def get_zerodha_service(api_key: str, api_secret: str) -> ZerodhaService:
    return ZerodhaService(api_key, api_secret)
