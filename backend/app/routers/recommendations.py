from datetime import datetime, timezone, date
from fastapi import APIRouter, HTTPException, BackgroundTasks
from sqlalchemy import select
from app.core.deps import CurrentUser, DbSession
from app.models.recommendation import Recommendation
from app.schemas.recommendation import RecommendationOut, TodayRecommendations, MarketOverview, SectorPerformance, NewsItem, AnalysisRequest
from app.services.market_data import MarketDataService
from app.services.sentiment import SentimentService
from app.services.analysis_runner import analyse_stock_for_user

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
_sentiment_svc = SentimentService()
_market_svc = MarketDataService()


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
    from app.models.portfolio import Holding
    holding = (await db.execute(
        select(Holding).where(
            Holding.user_id == current_user.id,
            Holding.tradingsymbol == payload.symbol.upper(),
            Holding.is_active == True,
        )
    )).scalar_one_or_none()

    rec = await analyse_stock_for_user(
        db, current_user,
        payload.symbol.upper(), payload.exchange, holding
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Could not fetch data for this symbol")
    return RecommendationOut.model_validate(rec)


@router.post("/run-all")
async def run_analysis_for_all_holdings(current_user: CurrentUser, db: DbSession):
    """Trigger analysis for every active holding in the user's portfolio."""
    from app.models.portfolio import Holding
    holdings = (await db.execute(
        select(Holding).where(Holding.user_id == current_user.id, Holding.is_active == True)
    )).scalars().all()

    if not holdings:
        raise HTTPException(status_code=400, detail="No holdings found. Add stocks to your portfolio first.")

    results = []
    for h in holdings:
        try:
            rec = await analyse_stock_for_user(db, current_user, h.tradingsymbol, h.exchange, h)
            if rec:
                results.append({"symbol": h.tradingsymbol, "signal": rec.signal.value})
        except Exception:
            results.append({"symbol": h.tradingsymbol, "signal": "ERROR"})

    return {"analysed": len(results), "results": results}


@router.get("/market-overview", response_model=MarketOverview)
async def get_market_overview():
    data = await _market_svc.get_market_overview()
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


@router.get("/sector-performance", response_model=list[SectorPerformance])
async def get_sector_performance():
    sectors = await _market_svc.get_sector_performance()
    return [SectorPerformance(**s) for s in sectors]


@router.get("/news", response_model=list[NewsItem])
async def get_market_news(symbol: str | None = None):
    if symbol:
        items = _sentiment_svc.get_news_for_symbol(symbol.upper())
    else:
        items = _sentiment_svc.get_market_news()
    return [NewsItem(**n) for n in items]
