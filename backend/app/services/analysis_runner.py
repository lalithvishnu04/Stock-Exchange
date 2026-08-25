"""Core analysis orchestrator – runs full stock analysis pipeline."""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.portfolio import Holding
from app.models.recommendation import Recommendation, RecommendationSignal, RiskLevel
from app.services.market_data import MarketDataService
from app.services.technical_analysis import TechnicalAnalysisService
from app.services.fundamental_analysis import FundamentalAnalysisService
from app.services.sentiment import SentimentService
from app.services.ai_engine import generate_recommendation
from app.services.portfolio_analyzer import PortfolioAnalyzer
from app.services.notifications import NotificationService

_technical_svc = TechnicalAnalysisService()
_fundamental_svc = FundamentalAnalysisService()
_sentiment_svc = SentimentService()
_portfolio_svc = PortfolioAnalyzer()
_notif_svc = NotificationService()
_market_svc = MarketDataService()


async def analyse_stock_for_user(
    db: AsyncSession,
    user: User,
    symbol: str,
    exchange: str = "NSE",
    holding: Holding | None = None,
) -> Recommendation | None:
    # Fetch market data
    stock_data = await _market_svc.get_stock_data(symbol, exchange)
    if not stock_data:
        return None

    # Technical analysis
    ohlcv = stock_data.get("ohlcv", {})
    technical = _technical_svc.analyze(ohlcv)

    # Fundamental analysis
    fundamental = _fundamental_svc.analyze(stock_data)

    # News sentiment
    news = _sentiment_svc.get_news_for_symbol(symbol, stock_data.get("company_name", ""))
    sentiment_agg = _sentiment_svc.aggregate_sentiment(news)

    # Portfolio context
    sector_allocs = await _portfolio_svc.get_sector_allocations(db, user.id)
    stock_allocs = await _portfolio_svc.get_stock_allocations(db, user.id)
    portfolio_ctx = _portfolio_svc.get_portfolio_context_for_stock(
        symbol, stock_data.get("sector", "Unknown"), stock_allocs, sector_allocs
    )

    holding_dict = None
    if holding:
        holding_dict = {
            "quantity": holding.quantity,
            "average_price": float(holding.average_price),
            "pnl_pct": float(holding.pnl_pct),
        }

    # AI recommendation
    rec_data = await generate_recommendation(
        stock_data, technical, fundamental, sentiment_agg, holding_dict, portfolio_ctx
    )

    current_price = stock_data.get("current_price", 0)

    rec = Recommendation(
        user_id=user.id,
        stock_symbol=symbol,
        stock_name=stock_data.get("company_name", symbol),
        sector=stock_data.get("sector", "Unknown"),
        exchange=exchange,
        signal=RecommendationSignal(rec_data["signal"]),
        risk_level=RiskLevel(rec_data["risk_level"]),
        confidence_score=rec_data.get("confidence_score", 50),
        current_price=current_price,
        target_price=rec_data.get("target_price"),
        stop_loss=rec_data.get("stop_loss"),
        upside_potential=rec_data.get("upside_potential_pct"),
        reason=rec_data.get("reason", ""),
        technical_summary=rec_data.get("technical_summary"),
        fundamental_summary=rec_data.get("fundamental_summary"),
        sentiment_summary=rec_data.get("sentiment_summary"),
        portfolio_allocation_pct=portfolio_ctx.get("stock_pct"),
        sector_allocation_pct=portfolio_ctx.get("sector_pct"),
        allocation_warning=rec_data.get("allocation_warning"),
    )
    db.add(rec)
    await db.flush()

    # Send alert for BUY/SELL signals
    if rec.signal in (RecommendationSignal.BUY, RecommendationSignal.SELL, RecommendationSignal.ADD_MORE):
        await _notif_svc.send_recommendation_alert(
            symbol=symbol,
            company_name=rec.stock_name,
            signal=rec.signal.value,
            risk_level=rec.risk_level.value,
            current_price=float(current_price),
            target_price=float(rec.target_price) if rec.target_price else None,
            stop_loss=float(rec.stop_loss) if rec.stop_loss else None,
            reason=rec.reason,
            chat_id=user.telegram_chat_id,
            email_to=user.email if user.email_alerts_enabled else None,
        )

    return rec


async def run_full_analysis_for_all_users(session_type: str = "scheduled"):
    async with AsyncSessionLocal() as db:
        try:
            users = (await db.execute(select(User).where(User.is_active == True))).scalars().all()
            for user in users:
                holdings = (
                    await db.execute(
                        select(Holding).where(Holding.user_id == user.id, Holding.is_active == True)
                    )
                ).scalars().all()
                for holding in holdings:
                    try:
                        await analyse_stock_for_user(db, user, holding.tradingsymbol, holding.exchange, holding)
                    except Exception:
                        pass
            await db.commit()
        except Exception:
            pass


async def run_intraday_check_for_all_users():
    """Lightweight intraday check – only flag stop-loss breaches."""
    async with AsyncSessionLocal() as db:
        try:
            users = (await db.execute(select(User).where(User.is_active == True))).scalars().all()
            for user in users:
                holdings = (
                    await db.execute(
                        select(Holding).where(Holding.user_id == user.id, Holding.is_active == True)
                    )
                ).scalars().all()
                for holding in holdings:
                    try:
                        stock_data = await _market_svc.get_stock_data(holding.tradingsymbol, holding.exchange, period="5d")
                        if not stock_data:
                            continue
                        cur_price = stock_data.get("current_price", 0)
                        avg = float(holding.average_price)
                        if avg > 0 and cur_price < avg * 0.93:
                            await _notif_svc.send_recommendation_alert(
                                symbol=holding.tradingsymbol,
                                company_name=holding.company_name,
                                signal="SELL",
                                risk_level="HIGH",
                                current_price=cur_price,
                                target_price=None,
                                stop_loss=round(avg * 0.93, 2),
                                reason=f"⚠️ Stop-loss breach: price ₹{cur_price:.2f} is >7% below your average ₹{avg:.2f}.",
                                chat_id=user.telegram_chat_id,
                                email_to=user.email if user.email_alerts_enabled else None,
                            )
                    except Exception:
                        pass
        except Exception:
            pass
