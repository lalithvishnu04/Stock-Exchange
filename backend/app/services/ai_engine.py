"""AI recommendation engine combining technical, fundamental, and sentiment signals."""
import json
from typing import Optional
from openai import AsyncOpenAI
from app.config import settings
from app.models.recommendation import RecommendationSignal, RiskLevel

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

SYSTEM_PROMPT = """
You are a SEBI-registered investment advisor specializing in Indian stock markets (NSE/BSE).
Your job is to analyze a stock and produce a structured investment recommendation.

IMPORTANT RULES (MUST FOLLOW):
1. You NEVER recommend putting more than 10% of portfolio in a single stock.
2. You NEVER recommend putting more than 25% of portfolio in a single sector.
3. You ALWAYS explain your recommendation in simple language a retail investor can understand.
4. You NEVER recommend investing entire capital in one stock.
5. Always assess risk: LOW (stable, low-volatility blue chip), MEDIUM (moderate volatility, some debt), HIGH (high volatility, speculative).
6. Recommendations must be one of: BUY, ADD_MORE, HOLD, PARTIAL_SELL, SELL, AVOID.
7. If there is any doubt, recommend HOLD over BUY. Protect capital first.
8. NEVER recommend BUY for a stock the user already holds ("current_holding" is not null) —
   use HOLD, ADD_MORE, PARTIAL_SELL, or SELL instead. BUY is reserved for new positions only,
   so existing holdings are never disturbed by a fresh buy suggestion.

Respond ONLY with valid JSON in the exact format specified.
"""

# Guidance injected per trade horizon so the same model adapts its reasoning
# instead of always producing swing-trade-style advice.
HORIZON_GUIDANCE = {
    "INTRADAY": (
        "Trade horizon: INTRADAY (same trading day only, position must close before market close). "
        "Prioritize price action, RSI-9, VWAP, and volume over fundamentals. Target/stop-loss must be tight "
        "(1-3% moves). Ignore long-term fundamentals almost entirely."
    ),
    "SWING": (
        "Trade horizon: SWING (hold for a few days to a few weeks). "
        "Balance technical momentum (RSI-14, MACD, moving averages) with fundamentals. "
        "Target/stop-loss should reflect a multi-day move (5-15%)."
    ),
    "LONGTERM": (
        "Trade horizon: LONG-TERM (hold for months to years). "
        "Weight fundamentals (growth, ROE, debt, valuation) and sector trend far more than short-term technicals. "
        "Target/stop-loss should reflect a large multi-month move (20%+ upside, wider stop-loss)."
    ),
}

# Horizon → target/stop-loss move size and scoring weights for the rule-based fallback.
_HORIZON_PROFILE = {
    "INTRADAY": {"target_pct": 0.02, "stop_pct": 0.01, "tech_weight": 1.5, "fund_weight": 0.0, "sent_weight": 0.3},
    "SWING": {"target_pct": 0.12, "stop_pct": 0.05, "tech_weight": 1.0, "fund_weight": 1.0, "sent_weight": 1.0},
    "LONGTERM": {"target_pct": 0.25, "stop_pct": 0.15, "tech_weight": 0.4, "fund_weight": 2.0, "sent_weight": 0.5},
}

RECOMMENDATION_SCHEMA = {
    "signal": "string: one of BUY, ADD_MORE, HOLD, PARTIAL_SELL, SELL, AVOID",
    "risk_level": "string: LOW, MEDIUM, or HIGH",
    "confidence_score": "number: 0-100",
    "target_price": "number or null",
    "stop_loss": "number or null",
    "upside_potential_pct": "number or null",
    "reason": "string: 2-3 sentence explanation in simple English for a retail investor",
    "technical_summary": "string: 1 sentence",
    "fundamental_summary": "string: 1 sentence",
    "sentiment_summary": "string: 1 sentence",
}


async def generate_recommendation(
    stock_data: dict,
    technical: dict,
    fundamental: dict,
    sentiment_agg: dict,
    holding: Optional[dict] = None,
    portfolio_context: Optional[dict] = None,
    horizon: str = "SWING",
) -> dict:
    """Call OpenAI to generate a recommendation, fall back to rule-based if no API key."""
    if not client:
        return _rule_based_recommendation(stock_data, technical, fundamental, sentiment_agg, holding, portfolio_context, horizon)

    context = {
        "trade_horizon": horizon,
        "stock": {
            "symbol": stock_data.get("symbol"),
            "company": stock_data.get("company_name"),
            "sector": stock_data.get("sector"),
            "current_price": stock_data.get("current_price"),
            "52w_high": stock_data.get("52w_high"),
            "52w_low": stock_data.get("52w_low"),
            "beta": stock_data.get("beta"),
        },
        "technical": {
            "overall": technical.get("overall"),
            "rsi": technical.get("rsi"),
            "macd_histogram": technical.get("macd_histogram"),
            "trend_strength": technical.get("trend_strength"),
            "volatility_annualised_pct": technical.get("volatility_annualised_pct"),
            "signals": technical.get("signals", []),
            "support": technical.get("support"),
            "resistance": technical.get("resistance"),
        },
        "fundamental": {
            "overall": fundamental.get("overall"),
            "pe_ratio": fundamental.get("pe_ratio"),
            "pb_ratio": fundamental.get("pb_ratio"),
            "roe_pct": fundamental.get("roe_pct"),
            "debt_to_equity": fundamental.get("debt_to_equity"),
            "revenue_growth_pct": fundamental.get("revenue_growth_pct"),
            "earnings_growth_pct": fundamental.get("earnings_growth_pct"),
            "signals": fundamental.get("signals", []),
            "warnings": fundamental.get("warnings", []),
        },
        "news_sentiment": sentiment_agg,
        "current_holding": holding,
        "portfolio_rules": {
            "max_single_stock_pct": settings.MAX_SINGLE_STOCK_ALLOCATION,
            "max_single_sector_pct": settings.MAX_SINGLE_SECTOR_ALLOCATION,
            "current_stock_allocation_pct": portfolio_context.get("stock_pct") if portfolio_context else None,
            "current_sector_allocation_pct": portfolio_context.get("sector_pct") if portfolio_context else None,
        },
    }

    user_msg = (
        f"Analyze the following stock and provide a recommendation.\n\n"
        f"Data:\n{json.dumps(context, indent=2)}\n\n"
        f"Respond ONLY with JSON matching this schema:\n{json.dumps(RECOMMENDATION_SCHEMA, indent=2)}"
    )

    system_prompt = f"{SYSTEM_PROMPT}\n{HORIZON_GUIDANCE.get(horizon, HORIZON_GUIDANCE['SWING'])}"
    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=800,
        )
        result = json.loads(response.choices[0].message.content)
        return _validate_and_apply_rules(result, portfolio_context, holding)
    except Exception as e:
        return _rule_based_recommendation(stock_data, technical, fundamental, sentiment_agg, holding, portfolio_context, horizon)


def _validate_and_apply_rules(
    result: dict, portfolio_context: Optional[dict], holding: Optional[dict] = None
) -> dict:
    """Enforce portfolio rules on AI output.

    Also enforces the "don't disturb existing holdings" rule: BUY is only ever
    valid for stocks you don't already own, and SELL/PARTIAL_SELL only make
    sense for stocks you do own.
    """
    signal = result.get("signal", "HOLD")
    warnings = []

    if holding:
        if signal == "BUY" or (signal == "ADD_MORE" and not settings.ALLOW_ADD_MORE_ON_HOLDINGS):
            warnings.append(
                "Already holding this stock; averaging-in is disabled "
                "(set ALLOW_ADD_MORE_ON_HOLDINGS=true to allow it)."
                if signal == "ADD_MORE"
                else "Already holding this stock; 'BUY' only applies to new positions."
            )
            signal = "HOLD"
    else:
        if signal in ("SELL", "PARTIAL_SELL", "ADD_MORE"):
            warnings.append("Not currently held; treating exit/add-more signal as AVOID.")
            signal = "AVOID"

    if portfolio_context:
        stock_pct = portfolio_context.get("stock_pct", 0)
        sector_pct = portfolio_context.get("sector_pct", 0)

        if stock_pct >= settings.MAX_SINGLE_STOCK_ALLOCATION and signal in ("BUY", "ADD_MORE"):
            signal = "HOLD"
            warnings.append(
                f"Position size limit: already at {stock_pct:.1f}% of portfolio "
                f"(max {settings.MAX_SINGLE_STOCK_ALLOCATION}%)"
            )

        if sector_pct >= settings.MAX_SINGLE_SECTOR_ALLOCATION and signal in ("BUY", "ADD_MORE"):
            signal = "HOLD"
            warnings.append(
                f"Sector limit: {portfolio_context.get('sector', 'this sector')} already at "
                f"{sector_pct:.1f}% (max {settings.MAX_SINGLE_SECTOR_ALLOCATION}%)"
            )

    result["signal"] = signal
    result["allocation_warning"] = "; ".join(warnings) if warnings else None
    return result


def _rule_based_recommendation(
    stock_data: dict,
    technical: dict,
    fundamental: dict,
    sentiment_agg: dict,
    holding: Optional[dict],
    portfolio_context: Optional[dict],
    horizon: str = "SWING",
) -> dict:
    """Fallback rule-based engine when OpenAI is unavailable."""
    profile = _HORIZON_PROFILE.get(horizon, _HORIZON_PROFILE["SWING"])
    tech_score = technical.get("bullish_score", 0) - technical.get("bearish_score", 0)
    fund_score = fundamental.get("score", 0)
    sent_score = 1 if sentiment_agg.get("overall") == "POSITIVE" else (-1 if sentiment_agg.get("overall") == "NEGATIVE" else 0)
    total = (
        tech_score * profile["tech_weight"]
        + fund_score * profile["fund_weight"]
        + sent_score * profile["sent_weight"]
    )

    volatility = technical.get("volatility_annualised_pct", 25)
    beta = stock_data.get("beta")
    risk_level = _calc_risk(volatility, beta)

    if total >= 6:
        signal = "BUY"
        reason = "Strong bullish technical and fundamental signals with positive sentiment."
    elif total >= 3:
        signal = "ADD_MORE" if holding else "BUY"
        reason = "Moderate bullish signals. Good entry opportunity with manageable risk."
    elif total >= 0:
        signal = "HOLD"
        reason = "Mixed signals. No clear direction; hold current position and monitor."
    elif total >= -3:
        signal = "PARTIAL_SELL"
        reason = "Weakening fundamentals or technicals. Consider booking partial profits."
    else:
        signal = "SELL"
        reason = "Significant bearish signals across multiple indicators. Recommend exit."

    current_price = stock_data.get("current_price", 0)
    target = round(current_price * (1 + profile["target_pct"]), 2) if signal in ("BUY", "ADD_MORE") else None
    stop_loss = round(current_price * (1 - profile["stop_pct"]), 2) if signal in ("BUY", "ADD_MORE") else None

    result = {
        "signal": signal,
        "risk_level": risk_level,
        "confidence_score": min(abs(total) * 10, 85),
        "target_price": target,
        "stop_loss": stop_loss,
        "upside_potential_pct": round((target - current_price) / current_price * 100, 2) if target else None,
        "reason": reason,
        "technical_summary": f"Technical outlook is {technical.get('overall', 'NEUTRAL')} "
                              f"with RSI at {technical.get('rsi', 50):.1f}.",
        "fundamental_summary": f"Fundamentals rated {fundamental.get('overall', 'HOLD')}.",
        "sentiment_summary": f"News sentiment is {sentiment_agg.get('overall', 'NEUTRAL')}.",
        "allocation_warning": None,
    }
    return _validate_and_apply_rules(result, portfolio_context, holding)


def _calc_risk(volatility: float, beta: float | None) -> str:
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
