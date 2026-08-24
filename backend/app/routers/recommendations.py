from datetime import datetime, timezone, date
from fastapi import APIRouter, HTTPException, BackgroundTasks
from sqlalchemy import select
import redis.asyncio as aioredis
from app.core.deps import CurrentUser, DbSession
from app.models.recommendation import Recommendation
from app.schemas.recommendation import RecommendationOut, TodayRecommendations, MarketOverview, SectorPerformance, NewsItem, AnalysisRequest
from app.services.market_data import MarketDataService
from app.services.sentiment import SentimentService
from app.services.analysis_runner import analyse_stock_for_user
from app.config import settings

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
_sentiment_svc = SentimentService()


def _get_redis() -> aioredis.Redis:
    return aioredis.from_url(settings.REDIS_URL, decode_responses=True)


@router.get("/today", response_model=TodayRecommendations)
async def get_today_recommendations(current_user: CurrentUser, db: DbSession):
    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
    result = await db.execute(
        select(Recommendation)
        .where(
            Recommendation.user_id == current_user.id,
            Recommendation.is_active == True,
            Recommendation.created_at >= today_start,
        )
        .order_by(Recommendation.confidence_score.desc())
    )
    recs = result.scalars().all()

    buy, add_more, hold, partial_sell, sell, avoid = [], [], [], [], [], []
    for r in recs:
        sig = r.signal.value
        if sig == "BUY":
            buy.append(r)
        elif sig == "ADD_MORE":
            add_more.append(r)
        elif sig == "HOLD":
            hold.append(r)
        elif sig == "PARTIAL_SELL":
            partial_sell.append(r)
        elif sig == "SELL":
            sell.append(r)
        elif sig == "AVOID":
            avoid.append(r)

    last_updated = recs[0].created_at if recs else None
    return TodayRecommendations(
        date=date.today().strftime("%d %B %Y"),
        buy=buy, add_more=add_more, hold=hold,
        partial_sell=partial_sell, sell=sell, avoid=avoid,
        total_count=len(recs),
        last_updated=last_updated,
    )


@router.get("/history", response_model=list[RecommendationOut])
async def get_recommendation_history(
    current_user: CurrentUser, db: DbSession,
    limit: int = 100, symbol: str | None = None,
):
    q = select(Recommendation).where(Recommendation.user_id == current_user.id)
    if symbol:
        q = q.where(Recommendation.stock_symbol == symbol.upper())
    q = q.order_by(Recommendation.created_at.desc()).limit(min(limit, 500))
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/analyse")
async def analyse_stock(
    payload: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DbSession,
):
    """Trigger on-demand analysis for a specific stock."""
    redis_client = _get_redis()
    from app.models.portfolio import Holding
    holding = (await db.execute(
        select(Holding).where(
            Holding.user_id == current_user.id,
            Holding.tradingsymbol == payload.symbol.upper(),
            Holding.is_active == True,
        )
    )).scalar_one_or_none()

    rec = await analyse_stock_for_user(
        db, redis_client, current_user,
        payload.symbol.upper(), payload.exchange, holding
    )
    await redis_client.aclose()
    if not rec:
        raise HTTPException(status_code=404, detail="Could not fetch data for this symbol")
    return RecommendationOut.model_validate(rec)


@router.get("/market-overview", response_model=MarketOverview)
async def get_market_overview():
    redis_client = _get_redis()
    try:
        svc = MarketDataService(redis_client)
        data = await svc.get_market_overview()
        n50 = data.get("NIFTY50", {})
        nb = data.get("NIFTYBANK", {})
        sx = data.get("SENSEX", {})
        mid = data.get("NIFTY_MIDCAP", {})
        return MarketOverview(
            nifty50=n50.get("price", 0),
            nifty50_change=n50.get("change", 0),
            nifty50_change_pct=n50.get("change_pct", 0),
            niftybank=nb.get("price", 0),
            niftybank_change=nb.get("change", 0),
            niftybank_change_pct=nb.get("change_pct", 0),
            sensex=sx.get("price", 0),
            sensex_change=sx.get("change", 0),
            sensex_change_pct=sx.get("change_pct", 0),
            nifty_midcap=mid.get("price", 0),
            nifty_midcap_change_pct=mid.get("change_pct", 0),
            market_status=data.get("market_status", "CLOSED"),
            as_of=datetime.fromisoformat(data.get("as_of", datetime.now(timezone.utc).isoformat())),
        )
    finally:
        await redis_client.aclose()


@router.get("/sector-performance", response_model=list[SectorPerformance])
async def get_sector_performance():
    redis_client = _get_redis()
    try:
        svc = MarketDataService(redis_client)
        sectors = await svc.get_sector_performance()
        return [SectorPerformance(**s) for s in sectors]
    finally:
        await redis_client.aclose()


@router.get("/news", response_model=list[NewsItem])
async def get_market_news(symbol: str | None = None):
    if symbol:
        items = _sentiment_svc.get_news_for_symbol(symbol.upper())
    else:
        items = _sentiment_svc.get_market_news()
    return [NewsItem(**n) for n in items]
