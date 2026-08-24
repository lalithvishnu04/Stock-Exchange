from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, field_validator


class HoldingCreate(BaseModel):
    tradingsymbol: str
    exchange: str = "NSE"
    quantity: int
    average_price: float

    @field_validator("tradingsymbol")
    @classmethod
    def upper_symbol(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("exchange")
    @classmethod
    def upper_exchange(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("quantity")
    @classmethod
    def positive_qty(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v

    @field_validator("average_price")
    @classmethod
    def positive_price(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Average price must be positive")
        return v


class HoldingUpdate(BaseModel):
    quantity: Optional[int] = None
    average_price: Optional[float] = None


class HoldingOut(BaseModel):
    id: int
    tradingsymbol: str
    exchange: str
    company_name: str
    sector: str
    industry: str
    quantity: int
    average_price: Decimal
    last_price: Decimal
    current_value: Decimal
    invested_value: Decimal
    pnl: Decimal
    pnl_pct: Decimal
    day_change: Decimal
    day_change_pct: Decimal
    portfolio_weight_pct: float
    last_synced_at: Optional[datetime]

    model_config = {"from_attributes": True}


class PortfolioSummary(BaseModel):
    total_invested: Decimal
    total_current_value: Decimal
    total_pnl: Decimal
    total_pnl_pct: float
    total_day_change: Decimal
    total_day_change_pct: float
    holdings_count: int
    last_synced_at: Optional[datetime]


class SectorAllocation(BaseModel):
    sector: str
    allocation_pct: float
    current_value: Decimal
    is_over_limit: bool   # > 25%
    stocks: list[str]


class StockAllocation(BaseModel):
    symbol: str
    company_name: str
    allocation_pct: float
    current_value: Decimal
    is_over_limit: bool   # > 10%


class AllocationRulesStatus(BaseModel):
    portfolio_summary: PortfolioSummary
    sector_allocations: list[SectorAllocation]
    stock_allocations: list[StockAllocation]
    violations: list[str]


class AlertLogOut(BaseModel):
    id: int
    alert_type: str
    subject: str
    message: str
    stock_symbol: Optional[str]
    signal: Optional[str]
    is_sent: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportOut(BaseModel):
    id: int
    report_type: str
    title: str
    report_date: datetime
    created_at: datetime
    file_path: Optional[str]

    model_config = {"from_attributes": True}
