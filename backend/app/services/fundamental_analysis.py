"""Fundamental analysis scoring from yfinance metrics."""
from typing import Optional


class FundamentalAnalysisService:

    def analyze(self, stock_data: dict) -> dict:
        pe = stock_data.get("pe_ratio")
        pb = stock_data.get("pb_ratio")
        roe = stock_data.get("roe")
        de = stock_data.get("debt_to_equity")
        rev_growth = stock_data.get("revenue_growth")
        earn_growth = stock_data.get("earnings_growth")
        div_yield = stock_data.get("dividend_yield")
        beta = stock_data.get("beta")

        score = 0
        signals = []
        warnings = []

        # ── Valuation ────────────────────────────────────────────────
        if pe is not None:
            if pe < 15:
                signals.append(f"Low P/E ({pe:.1f}) – potentially undervalued")
                score += 2
            elif 15 <= pe <= 25:
                signals.append(f"Moderate P/E ({pe:.1f}) – fairly valued")
                score += 1
            else:
                warnings.append(f"High P/E ({pe:.1f}) – may be overvalued")
                score -= 1

        if pb is not None:
            if pb < 1.5:
                signals.append(f"P/B below 1.5 ({pb:.2f}) – asset-backed")
                score += 1
            elif pb > 4:
                warnings.append(f"High P/B ({pb:.2f}) – expensive on book value")
                score -= 1

        # ── Profitability ────────────────────────────────────────────
        if roe is not None:
            roe_pct = roe * 100
            if roe_pct > 20:
                signals.append(f"High ROE ({roe_pct:.1f}%) – excellent profitability")
                score += 2
            elif roe_pct > 12:
                signals.append(f"Good ROE ({roe_pct:.1f}%)")
                score += 1
            else:
                warnings.append(f"Low ROE ({roe_pct:.1f}%) – weak profitability")

        # ── Debt ─────────────────────────────────────────────────────
        if de is not None:
            if de < 0.5:
                signals.append(f"Low Debt/Equity ({de:.2f}) – financially strong")
                score += 2
            elif de < 1.0:
                signals.append(f"Moderate Debt/Equity ({de:.2f})")
                score += 1
            elif de > 2.0:
                warnings.append(f"High Debt/Equity ({de:.2f}) – risky leverage")
                score -= 2

        # ── Growth ───────────────────────────────────────────────────
        if rev_growth is not None:
            rg = rev_growth * 100
            if rg > 15:
                signals.append(f"Strong revenue growth ({rg:.1f}%)")
                score += 2
            elif rg > 5:
                signals.append(f"Moderate revenue growth ({rg:.1f}%)")
                score += 1
            else:
                warnings.append(f"Weak revenue growth ({rg:.1f}%)")

        if earn_growth is not None:
            eg = earn_growth * 100
            if eg > 20:
                signals.append(f"Strong earnings growth ({eg:.1f}%)")
                score += 2
            elif eg > 5:
                signals.append(f"Moderate earnings growth ({eg:.1f}%)")
                score += 1
            else:
                warnings.append(f"Weak earnings growth ({eg:.1f}%)")

        # ── Dividends ────────────────────────────────────────────────
        if div_yield and div_yield > 0.02:
            signals.append(f"Dividend yield {div_yield*100:.1f}% – income generating")
            score += 1

        # ── Overall ──────────────────────────────────────────────────
        if score >= 6:
            overall = "STRONG_BUY"
        elif score >= 3:
            overall = "BUY"
        elif score >= 0:
            overall = "HOLD"
        elif score >= -2:
            overall = "SELL"
        else:
            overall = "STRONG_SELL"

        return {
            "overall": overall,
            "score": score,
            "signals": signals,
            "warnings": warnings,
            "pe_ratio": pe,
            "pb_ratio": pb,
            "roe_pct": round(roe * 100, 2) if roe else None,
            "debt_to_equity": de,
            "revenue_growth_pct": round(rev_growth * 100, 2) if rev_growth else None,
            "earnings_growth_pct": round(earn_growth * 100, 2) if earn_growth else None,
        }
