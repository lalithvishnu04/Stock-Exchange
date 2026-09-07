from datetime import datetime, timezone, date
from typing import Annotated
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user, get_db
from app.models.recommendation import Recommendation, TradeHorizon
from app.models.watchlist import Watchlist
from app.models.user import User
from app.schemas.recommendation import RecommendationOut, TodayRecommendations, MarketOverview, SectorPerformance, NewsItem, AnalysisRequest
from app.services.market_data import MarketDataService
from app.services.sentiment import SentimentService
from app.services.analysis_runner import analyse_stock_for_user

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
_sentiment_svc = SentimentService()
_market_svc = MarketDataService()


@router.get("/today", response_model=TodayRecommendations)
async def get_today_recommendations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    horizon: str | None = None,
):
    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
    conditions = [
        Recommendation.user_id == current_user.id,
        Recommendation.is_active == True,
        Recommendation.created_at >= today_start,
    ]
    if horizon:
        conditions.append(Recommendation.trade_horizon == TradeHorizon(horizon.upper()))
    result = await db.execute(
        select(Recommendation)
        .where(*conditions)
        .order_by(Recommendation.created_at.desc())
    )
    all_recs = result.scalars().all()

    # Defend against pre-existing duplicate rows (e.g. from before analysis
    # was made idempotent): keep only the most recent recommendation per symbol.
    seen_symbols: set[str] = set()
    recs = []
    for r in all_recs:
        if r.stock_symbol in seen_symbols:
            continue
        seen_symbols.add(r.stock_symbol)
        recs.append(r)
    recs.sort(key=lambda r: float(r.confidence_score), reverse=True)

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

    last_updated = all_recs[0].created_at if all_recs else None
    return TodayRecommendations(
        date=date.today().strftime("%d %B %Y"),
        buy=buy, add_more=add_more, hold=hold,
        partial_sell=partial_sell, sell=sell, avoid=avoid,
        total_count=len(recs),
        last_updated=last_updated,
    )


@router.get("/history", response_model=list[RecommendationOut])
async def get_recommendation_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 100,
    symbol: str | None = None,
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
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
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
        payload.symbol.upper(), payload.exchange, holding, payload.horizon.value
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Could not fetch data for this symbol")
    return RecommendationOut.model_validate(rec)


@router.post("/analyse-all")
async def analyse_all_holdings(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    horizon: str = "SWING",
):
    """Trigger analysis for all active holdings in the user's portfolio."""
    from app.models.portfolio import Holding
    holdings = (await db.execute(
        select(Holding).where(
            Holding.user_id == current_user.id,
            Holding.is_active == True,
        )
    )).scalars().all()
    
    results = []
    for holding in holdings:
        try:
            rec = await analyse_stock_for_user(
                db, current_user,
                holding.tradingsymbol, holding.exchange, holding, horizon.upper()
            )
            if rec:
                results.append(RecommendationOut.model_validate(rec))
        except Exception:
            # Skip failed analyses, continue with next holding
            pass
    
    await db.commit()
    return {"analysed": len(results), "recommendations": results}


@router.get("/market-picks")
async def get_market_picks(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    horizon: str = "SWING",
):
    """Recommendations for stocks the user doesn't already hold ("new buy" candidates).

    Reads pre-computed results from the scheduled market scan (see
    /market-picks/scan) instead of running hundreds of yfinance calls inline —
    scanning the full stock universe synchronously would time out the request.
    """
    from app.models.portfolio import Holding
    user_holdings = (await db.execute(
        select(Holding.tradingsymbol).where(
            Holding.user_id == current_user.id,
            Holding.is_active == True,
        )
    )).scalars().all()
    holding_symbols = set(s.upper() for s in user_holdings)

    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
    all_recs = (await db.execute(
        select(Recommendation)
        .where(
            Recommendation.user_id == current_user.id,
            Recommendation.trade_horizon == TradeHorizon(horizon.upper()),
            Recommendation.is_active == True,
            Recommendation.created_at >= today_start,
        )
        .order_by(Recommendation.confidence_score.desc())
    )).scalars().all()

    results = [r for r in all_recs if r.stock_symbol.upper() not in holding_symbols][:20]
    return [RecommendationOut.model_validate(r) for r in results]


@router.post("/market-picks/scan")
async def trigger_market_scan(
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
    horizon: str = "SWING",
):
    """Kick off a full ~190-stock universe scan in the background, ranked by
    confidence score so GET /market-picks returns genuine top picks rather than
    a fixed list. Runs async (non-blocking) since it takes a few minutes; poll
    GET /market-picks afterwards for results as they land.
    """
    from app.services.analysis_runner import run_market_scan_for_all_users
    background_tasks.add_task(run_market_scan_for_all_users, horizon.upper(), True)
    return {"message": "Full market scan started (~190 stocks, a few minutes) — refresh market picks shortly for top-ranked results."}


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


# ========== WATCHLIST ENDPOINTS ==========

from pydantic import BaseModel

class WatchlistItem(BaseModel):
    id: int
    stock_symbol: str
    stock_name: str
    exchange: str
    signal: str
    confidence_score: float
    current_price: float
    target_price: float | None
    added_at: datetime
    is_bought: bool
    
    class Config:
        from_attributes = True


class AddToWatchlistRequest(BaseModel):
    stock_symbol: str
    stock_name: str
    exchange: str = "NSE"
    signal: str
    confidence_score: float
    current_price: float
    target_price: float | None = None


@router.get("/watchlist", response_model=list[WatchlistItem])
async def get_watchlist(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get all watchlist items for the current user."""
    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.user_id == current_user.id, Watchlist.is_bought == False)
        .order_by(Watchlist.confidence_score.desc(), Watchlist.added_at.desc())
    )
    return result.scalars().all()


@router.post("/watchlist", response_model=WatchlistItem)
async def add_to_watchlist(
    payload: AddToWatchlistRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Add a stock to the user's watchlist."""
    # Check if already in watchlist
    existing = await db.execute(
        select(Watchlist).where(
            Watchlist.user_id == current_user.id,
            Watchlist.stock_symbol == payload.stock_symbol.upper(),
            Watchlist.is_bought == False,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already in watchlist")
    
    watchlist_item = Watchlist(
        user_id=current_user.id,
        stock_symbol=payload.stock_symbol.upper(),
        stock_name=payload.stock_name,
        exchange=payload.exchange,
        signal=payload.signal,
        confidence_score=payload.confidence_score,
        current_price=payload.current_price,
        target_price=payload.target_price,
    )
    db.add(watchlist_item)
    await db.flush()
    return WatchlistItem.model_validate(watchlist_item)


@router.delete("/watchlist/{watchlist_id}")
async def remove_from_watchlist(
    watchlist_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Remove a stock from the watchlist."""
    item = await db.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == current_user.id,
        )
    )
    watchlist_item = item.scalar_one_or_none()
    if not watchlist_item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    
    await db.delete(watchlist_item)
    await db.commit()
    return {"deleted": True}


@router.put("/watchlist/{watchlist_id}/mark-bought")
async def mark_as_bought(
    watchlist_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark a watchlist item as bought (move to portfolio)."""
    item = await db.execute(
        select(Watchlist).where(
            Watchlist.id == watchlist_id,
            Watchlist.user_id == current_user.id,
        )
    )
    watchlist_item = item.scalar_one_or_none()
    if not watchlist_item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    
    watchlist_item.is_bought = True
    watchlist_item.bought_at = datetime.now(timezone.utc)
    await db.commit()
    return WatchlistItem.model_validate(watchlist_item)
