"""Portfolio analysis & rule enforcement."""
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.portfolio import Holding
from app.config import settings


class PortfolioAnalyzer:

    async def get_holdings(self, db: AsyncSession, user_id: int) -> list[Holding]:
        result = await db.execute(
            select(Holding).where(Holding.user_id == user_id, Holding.is_active == True)
        )
        return list(result.scalars().all())

    async def get_summary(self, db: AsyncSession, user_id: int) -> dict:
        holdings = await self.get_holdings(db, user_id)
        if not holdings:
            return {
                "total_invested": 0, "total_current_value": 0,
                "total_pnl": 0, "total_pnl_pct": 0,
                "total_day_change": 0, "total_day_change_pct": 0,
                "holdings_count": 0, "last_synced_at": None,
            }
        total_inv = sum(float(h.invested_value) for h in holdings)
        total_cur = sum(float(h.current_value) for h in holdings)
        total_pnl = total_cur - total_inv
        pnl_pct = (total_pnl / total_inv * 100) if total_inv else 0
        day_chg = sum(float(h.day_change) * h.quantity for h in holdings)
        day_chg_pct = (day_chg / total_cur * 100) if total_cur else 0
        last_sync = max((h.last_synced_at for h in holdings if h.last_synced_at), default=None)

        return {
            "total_invested": round(total_inv, 2),
            "total_current_value": round(total_cur, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round(pnl_pct, 2),
            "total_day_change": round(day_chg, 2),
            "total_day_change_pct": round(day_chg_pct, 2),
            "holdings_count": len(holdings),
            "last_synced_at": last_sync,
        }

    async def get_sector_allocations(self, db: AsyncSession, user_id: int) -> list[dict]:
        holdings = await self.get_holdings(db, user_id)
        total = sum(float(h.current_value) for h in holdings) or 1

        sector_map: dict[str, dict] = {}
        for h in holdings:
            sector = h.sector or "Unknown"
            if sector not in sector_map:
                sector_map[sector] = {"current_value": 0.0, "stocks": []}
            sector_map[sector]["current_value"] += float(h.current_value)
            sector_map[sector]["stocks"].append(h.tradingsymbol)

        result = []
        for sector, data in sector_map.items():
            pct = round(data["current_value"] / total * 100, 2)
            result.append({
                "sector": sector,
                "allocation_pct": pct,
                "current_value": round(data["current_value"], 2),
                "is_over_limit": pct > settings.MAX_SINGLE_SECTOR_ALLOCATION,
                "stocks": data["stocks"],
            })
        return sorted(result, key=lambda x: x["allocation_pct"], reverse=True)

    async def get_stock_allocations(self, db: AsyncSession, user_id: int) -> list[dict]:
        holdings = await self.get_holdings(db, user_id)
        total = sum(float(h.current_value) for h in holdings) or 1

        result = []
        for h in holdings:
            pct = round(float(h.current_value) / total * 100, 2)
            result.append({
                "symbol": h.tradingsymbol,
                "company_name": h.company_name,
                "allocation_pct": pct,
                "current_value": round(float(h.current_value), 2),
                "is_over_limit": pct > settings.MAX_SINGLE_STOCK_ALLOCATION,
            })
        return sorted(result, key=lambda x: x["allocation_pct"], reverse=True)

    async def get_violations(self, db: AsyncSession, user_id: int) -> list[str]:
        violations = []
        sector_allocs = await self.get_sector_allocations(db, user_id)
        stock_allocs = await self.get_stock_allocations(db, user_id)

        for s in sector_allocs:
            if s["is_over_limit"]:
                violations.append(
                    f"Sector '{s['sector']}' at {s['allocation_pct']:.1f}% "
                    f"exceeds {settings.MAX_SINGLE_SECTOR_ALLOCATION}% limit"
                )
        for s in stock_allocs:
            if s["is_over_limit"]:
                violations.append(
                    f"Stock '{s['symbol']}' at {s['allocation_pct']:.1f}% "
                    f"exceeds {settings.MAX_SINGLE_STOCK_ALLOCATION}% limit"
                )
        return violations

    def get_portfolio_context_for_stock(
        self,
        symbol: str,
        sector: str,
        stock_allocations: list[dict],
        sector_allocations: list[dict],
    ) -> dict:
        stock_pct = next((s["allocation_pct"] for s in stock_allocations if s["symbol"] == symbol), 0.0)
        sector_pct = next((s["allocation_pct"] for s in sector_allocations if s["sector"] == sector), 0.0)
        return {"stock_pct": stock_pct, "sector_pct": sector_pct, "sector": sector}
