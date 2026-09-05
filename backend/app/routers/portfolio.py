from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from app.core.deps import CurrentUser, DbSession
from app.models.portfolio import Holding, AlertLog, Report
from app.schemas.portfolio import (
    HoldingOut, HoldingCreate, HoldingUpdate,
    PortfolioSummary, AllocationRulesStatus, AlertLogOut, ReportOut,
)
from app.services.portfolio_analyzer import PortfolioAnalyzer
from app.services.zerodha import lookup_stock, refresh_prices, ZerodhaService

router = APIRouter(prefix="/portfolio", tags=["portfolio"])
_portfolio_svc = PortfolioAnalyzer()


@router.post("/holdings", response_model=HoldingOut, status_code=201)
async def add_holding(payload: HoldingCreate, current_user: CurrentUser, db: DbSession):
    """Add a stock from your Zerodha portfolio manually."""
    # Verify symbol exists and fetch live data from Yahoo Finance (free)
    data = lookup_stock(payload.tradingsymbol, payload.exchange)
    if not data:
        raise HTTPException(status_code=404, detail=f"Symbol '{payload.tradingsymbol}' not found on {payload.exchange}. Check the symbol (e.g. RELIANCE, TCS, INFY).")

    # Upsert: if user already has this holding, update it
    existing = (await db.execute(
        select(Holding).where(
            Holding.user_id == current_user.id,
            Holding.tradingsymbol == payload.tradingsymbol,
            Holding.exchange == payload.exchange,
        )
    )).scalar_one_or_none()

    qty = payload.quantity
    avg = payload.average_price
    last = data["last_price"]
    cur_val = last * qty
    inv_val = avg * qty
    pnl = cur_val - inv_val
    pnl_pct = (pnl / inv_val * 100) if inv_val else 0
    now = datetime.now(timezone.utc)

    if existing:
        existing.quantity = qty
        existing.average_price = avg
        existing.last_price = last
        existing.close_price = data["close_price"]
        existing.current_value = cur_val
        existing.invested_value = inv_val
        existing.pnl = pnl
        existing.pnl_pct = pnl_pct
        existing.day_change = data["day_change"]
        existing.day_change_pct = data["day_change_pct"]
        existing.company_name = data["company_name"]
        existing.sector = data["sector"]
        existing.industry = data["industry"]
        existing.is_active = True
        existing.last_synced_at = now
        holding = existing
    else:
        holding = Holding(
            user_id=current_user.id,
            tradingsymbol=payload.tradingsymbol,
            exchange=payload.exchange,
            company_name=data["company_name"],
            sector=data["sector"],
            industry=data["industry"],
            quantity=qty,
            average_price=avg,
            last_price=last,
            close_price=data["close_price"],
            current_value=cur_val,
            invested_value=inv_val,
            pnl=pnl,
            pnl_pct=pnl_pct,
            day_change=data["day_change"],
            day_change_pct=data["day_change_pct"],
            portfolio_weight_pct=0.0,
            is_active=True,
            last_synced_at=now,
        )
        db.add(holding)

    await db.flush()
    await _recalc_weights(db, current_user.id)
    return holding


@router.put("/holdings/{holding_id}", response_model=HoldingOut)
async def update_holding(holding_id: int, payload: HoldingUpdate, current_user: CurrentUser, db: DbSession):
    holding = (await db.execute(
        select(Holding).where(Holding.id == holding_id, Holding.user_id == current_user.id)
    )).scalar_one_or_none()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")

    if payload.quantity is not None:
        holding.quantity = payload.quantity
    if payload.average_price is not None:
        holding.average_price = payload.average_price

    last = float(holding.last_price)
    qty = holding.quantity
    avg = float(holding.average_price)
    holding.invested_value = avg * qty
    holding.current_value = last * qty
    holding.pnl = holding.current_value - holding.invested_value
    holding.pnl_pct = (float(holding.pnl) / float(holding.invested_value) * 100) if holding.invested_value else 0

    await db.flush()
    await _recalc_weights(db, current_user.id)
    return holding


@router.delete("/holdings/{holding_id}", status_code=204)
async def delete_holding(holding_id: int, current_user: CurrentUser, db: DbSession):
    holding = (await db.execute(
        select(Holding).where(Holding.id == holding_id, Holding.user_id == current_user.id)
    )).scalar_one_or_none()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding not found")
    await db.delete(holding)
    await db.flush()
    await _recalc_weights(db, current_user.id)


@router.post("/refresh-prices")
async def refresh_portfolio_prices(current_user: CurrentUser, db: DbSession):
    """Refresh all holding prices from Yahoo Finance (free, no broker API)."""
    holdings = (await db.execute(
        select(Holding).where(Holding.user_id == current_user.id, Holding.is_active == True)
    )).scalars().all()

    if not holdings:
        return {"message": "No holdings to refresh", "count": 0}

    raw = [{"tradingsymbol": h.tradingsymbol, "exchange": h.exchange} for h in holdings]
    refreshed = refresh_prices(raw)
    price_map = {r["tradingsymbol"]: r for r in refreshed}
    now = datetime.now(timezone.utc)

    for h in holdings:
        data = price_map.get(h.tradingsymbol, {})
        if not data:
            continue
        last = data.get("last_price", float(h.last_price))
        h.last_price = last
        h.close_price = data.get("close_price", float(h.close_price))
        h.day_change = data.get("day_change", 0)
        h.day_change_pct = data.get("day_change_pct", 0)
        qty = h.quantity
        avg = float(h.average_price)
        h.current_value = last * qty
        h.invested_value = avg * qty
        h.pnl = float(h.current_value) - float(h.invested_value)
        h.pnl_pct = (float(h.pnl) / float(h.invested_value) * 100) if h.invested_value else 0
        h.last_synced_at = now

    await db.flush()
    await _recalc_weights(db, current_user.id)
    return {"message": "Prices refreshed from Yahoo Finance", "count": len(holdings)}


@router.get("/holdings", response_model=list[HoldingOut])
async def get_holdings(current_user: CurrentUser, db: DbSession):
    return await _portfolio_svc.get_holdings(db, current_user.id)


@router.get("/summary", response_model=PortfolioSummary)
async def get_summary(current_user: CurrentUser, db: DbSession):
    return await _portfolio_svc.get_summary(db, current_user.id)


@router.get("/allocations", response_model=AllocationRulesStatus)
async def get_allocations(current_user: CurrentUser, db: DbSession):
    return AllocationRulesStatus(
        portfolio_summary=await _portfolio_svc.get_summary(db, current_user.id),
        sector_allocations=await _portfolio_svc.get_sector_allocations(db, current_user.id),
        stock_allocations=await _portfolio_svc.get_stock_allocations(db, current_user.id),
        violations=await _portfolio_svc.get_violations(db, current_user.id),
    )


@router.get("/alerts", response_model=list[AlertLogOut])
async def get_alert_history(current_user: CurrentUser, db: DbSession, limit: int = 50):
    result = await db.execute(
        select(AlertLog)
        .where(AlertLog.user_id == current_user.id)
        .order_by(AlertLog.created_at.desc())
        .limit(min(limit, 200))
    )
    return result.scalars().all()


@router.get("/reports", response_model=list[ReportOut])
async def get_reports(current_user: CurrentUser, db: DbSession, limit: int = 30):
    result = await db.execute(
        select(Report)
        .where(Report.user_id == current_user.id)
        .order_by(Report.created_at.desc())
        .limit(min(limit, 100))
    )
    return result.scalars().all()


@router.get("/reports/{report_id}")
async def get_report_content(report_id: int, current_user: CurrentUser, db: DbSession):
    report = (await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == current_user.id)
    )).scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=report.content_html or "<p>No content</p>")


async def _recalc_weights(db: DbSession, user_id: int) -> None:
    """Recompute portfolio_weight_pct for all holdings after any change."""
    holdings = (await db.execute(
        select(Holding).where(Holding.user_id == user_id, Holding.is_active == True)
    )).scalars().all()
    total = sum(float(h.current_value) for h in holdings) or 1
    for h in holdings:
        h.portfolio_weight_pct = round(float(h.current_value) / total * 100, 3)
    await db.flush()


@router.get("/sync")
async def sync_portfolio(current_user: CurrentUser, db: DbSession):
    """Sync holdings from Zerodha."""
    if not current_user.zerodha_access_token:
        raise HTTPException(status_code=400, detail="Zerodha not connected")
    if not current_user.zerodha_api_key:
        raise HTTPException(status_code=400, detail="Zerodha API key missing")

    svc = ZerodhaService(current_user.zerodha_api_key, current_user.zerodha_api_secret or "")
    svc.set_access_token(current_user.zerodha_access_token)
    raw_holdings = svc.get_holdings()

    if not raw_holdings:
        return {"message": "No holdings found or Zerodha token expired", "count": 0}

    # Mark all existing holdings inactive
    await db.execute(
        Holding.__table__.update()
        .where(Holding.user_id == current_user.id)
        .values(is_active=False)
    )

    total_value = sum(
        (float(h.get("last_price", 0)) * int(h.get("quantity", 0))) for h in raw_holdings
    ) or 1

    now = datetime.now(timezone.utc)
    for h in raw_holdings:
        qty = int(h.get("quantity", 0))
        avg = float(h.get("average_price", 0))
        last = float(h.get("last_price", 0))
        close = float(h.get("close_price", last))
        cur_val = last * qty
        inv_val = avg * qty
        pnl = cur_val - inv_val
        pnl_pct = (pnl / inv_val * 100) if inv_val else 0
        day_chg = last - close
        day_chg_pct = (day_chg / close * 100) if close else 0
        weight = (cur_val / total_value * 100)

        existing = (await db.execute(
            select(Holding).where(
                Holding.user_id == current_user.id,
                Holding.tradingsymbol == h["tradingsymbol"],
            )
        )).scalar_one_or_none()

        if existing:
            existing.quantity = qty
            existing.average_price = avg
            existing.last_price = last
            existing.close_price = close
            existing.current_value = cur_val
            existing.invested_value = inv_val
            existing.pnl = pnl
            existing.pnl_pct = pnl_pct
            existing.day_change = day_chg
            existing.day_change_pct = day_chg_pct
            existing.portfolio_weight_pct = weight
            existing.is_active = True
            existing.last_synced_at = now
        else:
            db.add(Holding(
                user_id=current_user.id,
                tradingsymbol=h["tradingsymbol"],
                exchange=h.get("exchange", "NSE"),
                isin=h.get("isin"),
                instrument_token=h.get("instrument_token"),
                company_name=h.get("tradingsymbol", ""),
                sector="Unknown",
                quantity=qty,
                average_price=avg,
                last_price=last,
                close_price=close,
                current_value=cur_val,
                invested_value=inv_val,
                pnl=pnl,
                pnl_pct=pnl_pct,
                day_change=day_chg,
                day_change_pct=day_chg_pct,
                portfolio_weight_pct=weight,
                is_active=True,
                last_synced_at=now,
            ))

    await db.flush()
    return {"message": "Portfolio synced", "count": len(raw_holdings)}
