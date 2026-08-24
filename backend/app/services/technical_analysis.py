"""Technical analysis indicators using pandas_ta."""
from typing import Optional
import pandas as pd
import pandas_ta as ta
import numpy as np


class TechnicalAnalysisService:

    def analyze(self, ohlcv: dict) -> dict:
        """ohlcv: dict with lists of open/high/low/close/volume."""
        if not ohlcv or len(ohlcv.get("close", [])) < 20:
            return {"error": "Insufficient data"}

        df = pd.DataFrame({
            "open": ohlcv["open"],
            "high": ohlcv["high"],
            "low": ohlcv["low"],
            "close": ohlcv["close"],
            "volume": ohlcv["volume"],
        })
        df.index = pd.to_datetime(ohlcv.get("dates", range(len(df))))

        # ── Moving Averages ──────────────────────────────────────────
        df.ta.sma(length=20, append=True)
        df.ta.sma(length=50, append=True)
        df.ta.ema(length=20, append=True)
        df.ta.ema(length=50, append=True)

        # ── Momentum ─────────────────────────────────────────────────
        df.ta.rsi(length=14, append=True)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)

        # ── Volatility ───────────────────────────────────────────────
        df.ta.bbands(length=20, std=2, append=True)
        df.ta.atr(length=14, append=True)

        # ── Volume ───────────────────────────────────────────────────
        df.ta.obv(append=True)

        # ── Trend ────────────────────────────────────────────────────
        df.ta.adx(length=14, append=True)

        last = df.iloc[-1]
        close = float(last["close"])

        rsi = float(last.get("RSI_14", 50) or 50)
        macd_val = float(last.get("MACD_12_26_9", 0) or 0)
        macd_signal = float(last.get("MACDs_12_26_9", 0) or 0)
        macd_hist = float(last.get("MACDh_12_26_9", 0) or 0)
        sma20 = float(last.get("SMA_20", close) or close)
        sma50 = float(last.get("SMA_50", close) or close)
        ema20 = float(last.get("EMA_20", close) or close)
        bb_upper = float(last.get("BBU_20_2.0", close * 1.02) or close * 1.02)
        bb_lower = float(last.get("BBL_20_2.0", close * 0.98) or close * 0.98)
        adx = float(last.get("ADX_14", 25) or 25)

        # ── Signals ──────────────────────────────────────────────────
        signals = []
        bullish_count = 0
        bearish_count = 0

        # RSI
        if rsi < 30:
            signals.append("RSI Oversold (Buy signal)")
            bullish_count += 2
        elif rsi > 70:
            signals.append("RSI Overbought (Sell signal)")
            bearish_count += 2
        elif 30 <= rsi <= 45:
            signals.append("RSI approaching oversold")
            bullish_count += 1
        elif 55 <= rsi <= 70:
            signals.append("RSI approaching overbought")
            bearish_count += 1

        # MACD
        if macd_val > macd_signal and macd_hist > 0:
            signals.append("MACD bullish crossover")
            bullish_count += 2
        elif macd_val < macd_signal and macd_hist < 0:
            signals.append("MACD bearish crossover")
            bearish_count += 2

        # Price vs MAs
        if close > sma20 > sma50:
            signals.append("Price above SMA20 & SMA50 – uptrend")
            bullish_count += 2
        elif close < sma20 < sma50:
            signals.append("Price below SMA20 & SMA50 – downtrend")
            bearish_count += 2

        # Bollinger Band squeeze
        if close <= bb_lower * 1.01:
            signals.append("Near Bollinger lower band – potential bounce")
            bullish_count += 1
        elif close >= bb_upper * 0.99:
            signals.append("Near Bollinger upper band – potential resistance")
            bearish_count += 1

        # ADX trend strength
        trend_strength = "Strong" if adx > 25 else "Weak"

        # ── Support / Resistance (20-day range) ──────────────────────
        recent = df.tail(20)
        support = float(recent["low"].min())
        resistance = float(recent["high"].max())

        # ── Overall technical sentiment ───────────────────────────────
        if bullish_count > bearish_count + 1:
            overall = "BULLISH"
        elif bearish_count > bullish_count + 1:
            overall = "BEARISH"
        else:
            overall = "NEUTRAL"

        # ── Volatility (annualised) ───────────────────────────────────
        returns = df["close"].pct_change().dropna()
        volatility = float(returns.std() * np.sqrt(252) * 100)

        return {
            "overall": overall,
            "rsi": round(rsi, 2),
            "macd": round(macd_val, 4),
            "macd_signal": round(macd_signal, 4),
            "macd_histogram": round(macd_hist, 4),
            "sma20": round(sma20, 2),
            "sma50": round(sma50, 2),
            "ema20": round(ema20, 2),
            "bb_upper": round(bb_upper, 2),
            "bb_lower": round(bb_lower, 2),
            "adx": round(adx, 2),
            "trend_strength": trend_strength,
            "support": round(support, 2),
            "resistance": round(resistance, 2),
            "volatility_annualised_pct": round(volatility, 2),
            "signals": signals,
            "bullish_score": bullish_count,
            "bearish_score": bearish_count,
        }

    def get_risk_level(self, volatility: float, beta: float | None = None) -> str:
        score = 0
        if volatility > 40:
            score += 2
        elif volatility > 25:
            score += 1

        if beta is not None:
            if beta > 1.5:
                score += 2
            elif beta > 1.0:
                score += 1

        if score >= 3:
            return "HIGH"
        if score >= 1:
            return "MEDIUM"
        return "LOW"
