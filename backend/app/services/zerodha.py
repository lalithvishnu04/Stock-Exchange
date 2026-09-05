"""Free portfolio price refresh using yfinance – no broker API needed."""
from datetime import datetime, timezone
from typing import Optional
import yfinance as yf

# Sector overrides for ETFs and instruments Yahoo Finance misclassifies
_SECTOR_OVERRIDES: dict[str, tuple[str, str]] = {
    "GOLDBEES": ("Gold ETF", "Commodities ETF"),
    "LIQUIDBEES": ("Liquid ETF", "Debt ETF"),
    "JUNIORBEES": ("Equity ETF", "Index ETF"),
    "NIFTYBEES": ("Equity ETF", "Index ETF"),
    "BANKBEES": ("Banking ETF", "Index ETF"),
    "ITBEES": ("IT ETF", "Index ETF"),
    "SETFNIF50": ("Equity ETF", "Index ETF"),
    "SETFNN50": ("Equity ETF", "Index ETF"),
    "ICICIB22": ("Equity ETF", "Index ETF"),
    "MOM100": ("Equity ETF", "Momentum ETF"),
}


def _yf_symbol(symbol: str, exchange: str) -> str:
    if exchange.upper() == "BSE":
        return f"{symbol}.BO"
    return f"{symbol}.NS"   # NSE default


def _live_quote(ticker: "yf.Ticker", info: dict) -> tuple[float, float] | None:
    """Real-time-ish last/previous price from Yahoo's quote endpoint.

    Prefer this over the daily historical 'Close' bar, which can lag a full
    session behind (Yahoo sometimes hasn't finalized today's bar yet), causing
    the app's LTP to diverge noticeably from the broker's actual LTP.
    """
    try:
        fast = ticker.fast_info
        last = fast.get("last_price") or fast.get("lastPrice")
        prev = fast.get("previous_close") or fast.get("previousClose") or fast.get("regularMarketPreviousClose")
        if last:
            return float(last), float(prev) if prev else float(last)
    except Exception:
        pass
    last = info.get("currentPrice") or info.get("regularMarketPrice")
    prev = info.get("regularMarketPreviousClose") or info.get("previousClose")
    if last:
        return float(last), float(prev) if prev else float(last)
    return None


def lookup_stock(symbol: str, exchange: str = "NSE") -> dict | None:
    """Fetch current price + metadata for a symbol. Returns None if not found."""
    ticker = yf.Ticker(_yf_symbol(symbol, exchange))
    info = ticker.info or {}
    quote = _live_quote(ticker, info)
    if quote:
        last, prev = quote
    else:
        hist = ticker.history(period="2d")
        if hist.empty:
            return None
        last = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else last
    sector_override = _SECTOR_OVERRIDES.get(symbol.upper())
    return {
        "symbol": symbol.upper(),
        "exchange": exchange.upper(),
        "company_name": info.get("longName") or info.get("shortName") or symbol.upper(),
        "sector": sector_override[0] if sector_override else (info.get("sector") or "Unknown"),
        "industry": sector_override[1] if sector_override else (info.get("industry") or "Unknown"),
        "last_price": round(last, 2),
        "close_price": round(prev, 2),
        "day_change": round(last - prev, 2),
        "day_change_pct": round((last - prev) / prev * 100, 2) if prev else 0.0,
    }


def refresh_prices(holdings: list[dict]) -> list[dict]:
    """Refresh last_price for a list of {symbol, exchange} dicts using yfinance.

    Fetches each symbol's live quote individually (fast_info/info) rather than a
    bulk daily-bar download, since the live quote tracks the broker's actual LTP
    much more closely than the historical 'Close' column.
    """
    if not holdings:
        return []

    results = []
    for h in holdings:
        yf_sym = _yf_symbol(h["tradingsymbol"], h.get("exchange", "NSE"))
        try:
            ticker = yf.Ticker(yf_sym)
            info = ticker.info or {}
            quote = _live_quote(ticker, info)
            if quote:
                last, prev = quote
            else:
                hist = ticker.history(period="2d")
                if hist.empty:
                    results.append(h)
                    continue
                last = float(hist["Close"].iloc[-1])
                prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else last
            h["last_price"] = round(last, 2)
            h["close_price"] = round(prev, 2)
            h["day_change"] = round(last - prev, 2)
            h["day_change_pct"] = round((last - prev) / prev * 100, 2) if prev else 0.0
        except Exception:
            pass
        results.append(h)
    return results


def get_zerodha_service(api_key: str, api_secret: str) -> "ZerodhaService":
    return ZerodhaService(api_key, api_secret)


class ZerodhaService:
    """Stub — no live Zerodha API; uses yfinance for market data."""

    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self._access_token: str | None = None

    def set_access_token(self, token: str) -> None:
        self._access_token = token

    def get_holdings(self) -> list[dict]:
        """Returns empty list — live Zerodha holdings require a valid access token."""
        return []

    def generate_session(self, request_token: str) -> dict:
        raise NotImplementedError("Live Zerodha session not supported; configure API credentials in Zerodha developer console.")
