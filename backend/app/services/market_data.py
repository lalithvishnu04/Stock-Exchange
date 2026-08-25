"""Market data fetching via yfinance with in-memory cache (Redis optional)."""
import time
import json
from datetime import datetime, timezone
from typing import Optional
import pandas as pd
import yfinance as yf
from app.config import settings


def to_yf_symbol(symbol: str, exchange: str = "NSE") -> str:
    if exchange.upper() == "NSE":
        return f"{symbol}.NS"
    if exchange.upper() == "BSE":
        return f"{symbol}.BO"
    return symbol


INDEX_SYMBOLS = {
    "NIFTY50": "^NSEI",
    "NIFTYBANK": "^NSEBANK",
    "SENSEX": "^BSESN",
    "NIFTY_MIDCAP": "^NSEMDCP50",
}

SECTOR_ETF_MAP = {
    "IT": "NIFTYIT.NS",
    "Banking": "BANKNIFTY.NS",
    "Pharma": "NIFTYPHARMA.NS",
    "Auto": "NIFTYAUTO.NS",
    "FMCG": "NIFTYFMCG.NS",
    "Metal": "NIFTYMETAL.NS",
    "Realty": "NIFTYREALTY.NS",
    "Energy": "NIFTYENERGY.NS",
}

# Simple in-memory cache: key → (data, expires_at_timestamp)
_mem_cache: dict = {}


class MarketDataService:
    def __init__(self):
        self.ttl = settings.CACHE_TTL_SECONDS

    async def _get_cached(self, key: str) -> Optional[dict]:
        entry = _mem_cache.get(key)
        if entry and time.monotonic() < entry[1]:
            return entry[0]
        return None

    async def _set_cache(self, key: str, data: dict, ttl: int | None = None) -> None:
        _mem_cache[key] = (data, time.monotonic() + (ttl or self.ttl))

    async def get_market_overview(self) -> dict:
        cached = await self._get_cached("market:overview")
        if cached:
            return cached

        result = {}
        tickers = yf.download(
            list(INDEX_SYMBOLS.values()),
            period="2d",
            interval="1d",
            progress=False,
            group_by="ticker",
        )

        def _extract(sym: str, yf_sym: str) -> dict:
            try:
                df = tickers[yf_sym] if len(INDEX_SYMBOLS) > 1 else tickers
                last = float(df["Close"].iloc[-1])
                prev = float(df["Close"].iloc[-2])
                chg = last - prev
                chg_pct = (chg / prev) * 100
                return {"price": round(last, 2), "change": round(chg, 2), "change_pct": round(chg_pct, 2)}
            except Exception:
                return {"price": 0.0, "change": 0.0, "change_pct": 0.0}

        for name, sym in INDEX_SYMBOLS.items():
            result[name] = _extract(name, sym)

        result["as_of"] = datetime.now(timezone.utc).isoformat()
        now = datetime.now(timezone.utc)
        # Market is OPEN Mon-Fri 9:15-15:30 IST (UTC+5:30)
        ist_hour = (now.hour + 5) % 24
        ist_minute = (now.minute + 30) % 60
        ist_time = ist_hour * 60 + ist_minute
        if now.weekday() < 5 and 555 <= ist_time <= 930:
            result["market_status"] = "OPEN"
        else:
            result["market_status"] = "CLOSED"

        await self._set_cache("market:overview", result, ttl=120)
        return result

    async def get_stock_data(
        self,
        symbol: str,
        exchange: str = "NSE",
        period: str = "1y",
    ) -> dict:
        key = f"stock:{symbol}:{exchange}:{period}"
        cached = await self._get_cached(key)
        if cached:
            return cached

        yf_sym = to_yf_symbol(symbol, exchange)
        ticker = yf.Ticker(yf_sym)
        hist = ticker.history(period=period)
        info = ticker.info or {}

        if hist.empty:
            return {}

        data = {
            "symbol": symbol,
            "exchange": exchange,
            "company_name": info.get("longName", symbol),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "current_price": float(hist["Close"].iloc[-1]),
            "prev_close": float(hist["Close"].iloc[-2]) if len(hist) > 1 else 0,
            "open": float(hist["Open"].iloc[-1]),
            "high": float(hist["High"].iloc[-1]),
            "low": float(hist["Low"].iloc[-1]),
            "volume": int(hist["Volume"].iloc[-1]),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "pb_ratio": info.get("priceToBook"),
            "dividend_yield": info.get("dividendYield"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "avg_volume": info.get("averageVolume"),
            "beta": info.get("beta"),
            "roe": info.get("returnOnEquity"),
            "roce": info.get("returnOnAssets"),
            "debt_to_equity": info.get("debtToEquity"),
            "eps": info.get("trailingEps"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "ohlcv": {
                "dates": hist.index.strftime("%Y-%m-%d").tolist(),
                "open": hist["Open"].round(2).tolist(),
                "high": hist["High"].round(2).tolist(),
                "low": hist["Low"].round(2).tolist(),
                "close": hist["Close"].round(2).tolist(),
                "volume": hist["Volume"].tolist(),
            },
        }
        await self._set_cache(key, data)
        return data

    async def get_sector_performance(self) -> list[dict]:
        cached = await self._get_cached("market:sectors")
        if cached:
            return cached

        result = []
        for sector, etf in SECTOR_ETF_MAP.items():
            try:
                df = yf.download(etf, period="2d", interval="1d", progress=False)
                if not df.empty and len(df) >= 2:
                    last = float(df["Close"].iloc[-1])
                    prev = float(df["Close"].iloc[-2])
                    chg_pct = round((last - prev) / prev * 100, 2)
                    sentiment = "BULLISH" if chg_pct > 0.3 else "BEARISH" if chg_pct < -0.3 else "NEUTRAL"
                    result.append({"sector": sector, "change_pct": chg_pct, "sentiment": sentiment})
            except Exception:
                result.append({"sector": sector, "change_pct": 0.0, "sentiment": "NEUTRAL"})

        await self._set_cache("market:sectors", result, ttl=600)
        return result
