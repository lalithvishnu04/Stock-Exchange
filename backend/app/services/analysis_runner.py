"""Core analysis orchestrator – runs full stock analysis pipeline."""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.portfolio import Holding
from app.models.recommendation import Recommendation, RecommendationSignal, RiskLevel, TradeHorizon
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
    horizon: str = "SWING",
) -> Recommendation | None:
    # Fetch market data using candles appropriate for this trade horizon
    stock_data = await _market_svc.get_stock_data_for_horizon(symbol, exchange, horizon)
    if not stock_data:
        return None

    # Technical analysis
    ohlcv = stock_data.get("ohlcv", {})
    technical = _technical_svc.analyze(ohlcv, horizon)

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
        stock_data, technical, fundamental, sentiment_agg, holding_dict, portfolio_ctx, horizon
    )

    current_price = stock_data.get("current_price", 0)

    # Upsert: reuse today's existing recommendation for this symbol+horizon instead of
    # inserting a new row every time analysis runs (pre-market/post-market/intraday
    # polling and manual "analyse" all hit this same symbol repeatedly per day).
    today_start = datetime.combine(datetime.now(timezone.utc).date(), datetime.min.time()).replace(tzinfo=timezone.utc)
    existing = (await db.execute(
        select(Recommendation).where(
            Recommendation.user_id == user.id,
            Recommendation.stock_symbol == symbol,
            Recommendation.trade_horizon == TradeHorizon(horizon),
            Recommendation.is_active == True,
            Recommendation.created_at >= today_start,
        )
    )).scalar_one_or_none()

    rec = existing or Recommendation(user_id=user.id, stock_symbol=symbol, trade_horizon=TradeHorizon(horizon))
    rec.stock_name = stock_data.get("company_name", symbol)
    rec.sector = stock_data.get("sector", "Unknown")
    rec.exchange = exchange
    rec.signal = RecommendationSignal(rec_data["signal"])
    rec.risk_level = RiskLevel(rec_data["risk_level"])
    rec.confidence_score = rec_data.get("confidence_score", 50)
    rec.current_price = current_price
    rec.target_price = rec_data.get("target_price")
    rec.stop_loss = rec_data.get("stop_loss")
    rec.upside_potential = rec_data.get("upside_potential_pct")
    rec.reason = rec_data.get("reason", "")
    rec.technical_summary = rec_data.get("technical_summary")
    rec.fundamental_summary = rec_data.get("fundamental_summary")
    rec.sentiment_summary = rec_data.get("sentiment_summary")
    rec.portfolio_allocation_pct = portfolio_ctx.get("stock_pct")
    rec.sector_allocation_pct = portfolio_ctx.get("sector_pct")
    rec.allocation_warning = rec_data.get("allocation_warning")
    if not existing:
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


async def refresh_holdings_for_all_users():
    """Refresh last_price/current_value for every active holding (Yahoo Finance).

    Holding prices were previously only updated via the manual "Refresh Prices"
    button, so the dashboard would silently drift from real broker prices unless
    the user clicked it. Scheduler calls this on a cadence to keep them current.
    """
    from app.services.zerodha import refresh_prices as _refresh_prices

    async with AsyncSessionLocal() as db:
        try:
            users = (await db.execute(select(User).where(User.is_active == True))).scalars().all()
            for user in users:
                holdings = (
                    await db.execute(
                        select(Holding).where(Holding.user_id == user.id, Holding.is_active == True)
                    )
                ).scalars().all()
                if not holdings:
                    continue

                raw = [{"tradingsymbol": h.tradingsymbol, "exchange": h.exchange} for h in holdings]
                refreshed = _refresh_prices(raw)
                price_map = {r["tradingsymbol"]: r for r in refreshed}
                now = datetime.now(timezone.utc)

                for h in holdings:
                    data = price_map.get(h.tradingsymbol)
                    if not data:
                        continue
                    last = data.get("last_price", float(h.last_price))
                    qty = h.quantity
                    avg = float(h.average_price)
                    h.last_price = last
                    h.close_price = data.get("close_price", float(h.close_price))
                    h.day_change = data.get("day_change", 0)
                    h.day_change_pct = data.get("day_change_pct", 0)
                    h.current_value = last * qty
                    h.invested_value = avg * qty
                    h.pnl = float(h.current_value) - float(h.invested_value)
                    h.pnl_pct = (float(h.pnl) / float(h.invested_value) * 100) if h.invested_value else 0
                    h.last_synced_at = now

                total = sum(float(h.current_value) for h in holdings) or 1
                for h in holdings:
                    h.portfolio_weight_pct = round(float(h.current_value) / total * 100, 3)
            await db.commit()
        except Exception:
            pass


async def run_full_analysis_for_all_users(session_type: str = "scheduled"):
    """Runs SWING and LONG-TERM horizon analysis for every active holding."""
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
                    for horizon in ("SWING", "LONGTERM"):
                        try:
                            await analyse_stock_for_user(db, user, holding.tradingsymbol, holding.exchange, holding, horizon)
                        except Exception:
                            pass
            await db.commit()
        except Exception:
            pass


async def run_intraday_check_for_all_users():
    """Runs INTRADAY horizon analysis for holdings and flags stop-loss breaches."""
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
                        await analyse_stock_for_user(db, user, holding.tradingsymbol, holding.exchange, holding, "INTRADAY")
                    except Exception:
                        pass
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
            await db.commit()
        except Exception:
            pass


async def run_market_scan_for_all_users(horizon: str = "SWING"):
    """Scans the full stock universe (excluding each user's current holdings) and
    stores recommendations, so /market-picks can just read pre-computed results
    instead of running hundreds of yfinance calls inside an HTTP request.
    """
    from app.data.stock_universe import STOCK_UNIVERSE

    async with AsyncSessionLocal() as db:
        try:
            users = (await db.execute(select(User).where(User.is_active == True))).scalars().all()
            for user in users:
                held = set((await db.execute(
                    select(Holding.tradingsymbol).where(Holding.user_id == user.id, Holding.is_active == True)
                )).scalars().all())
                for symbol in STOCK_UNIVERSE:
                    if symbol in held:
                        continue
                    try:
                        await analyse_stock_for_user(db, user, symbol, "NSE", holding=None, horizon=horizon)
                        await db.commit()
                    except Exception:
                        await db.rollback()
        except Exception:
            pass
