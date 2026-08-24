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

Respond ONLY with valid JSON in the exact format specified.
"""

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
) -> dict:
    """Call OpenAI to generate a recommendation, fall back to rule-based if no API key."""
    if not client:
        return _rule_based_recommendation(stock_data, technical, fundamental, sentiment_agg, holding, portfolio_context)

    context = {
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

    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=800,
        )
        result = json.loads(response.choices[0].message.content)
        return _validate_and_apply_rules(result, portfolio_context)
    except Exception as e:
        return _rule_based_recommendation(stock_data, technical, fundamental, sentiment_agg, holding, portfolio_context)


def _validate_and_apply_rules(result: dict, portfolio_context: Optional[dict]) -> dict:
    """Enforce portfolio rules on AI output."""
    signal = result.get("signal", "HOLD")
    warnings = []

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
) -> dict:
    """Fallback rule-based engine when OpenAI is unavailable."""
    tech_score = technical.get("bullish_score", 0) - technical.get("bearish_score", 0)
    fund_score = fundamental.get("score", 0)
    sent_score = 1 if sentiment_agg.get("overall") == "POSITIVE" else (-1 if sentiment_agg.get("overall") == "NEGATIVE" else 0)
    total = tech_score + fund_score + sent_score

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
    target = round(current_price * 1.15, 2) if signal in ("BUY", "ADD_MORE") else None
    stop_loss = round(current_price * 0.93, 2) if signal in ("BUY", "ADD_MORE") else None

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
    return _validate_and_apply_rules(result, portfolio_context)


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
