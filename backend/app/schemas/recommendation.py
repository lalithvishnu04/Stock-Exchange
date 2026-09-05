from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel
from app.models.recommendation import RecommendationSignal, RiskLevel, TradeHorizon


class RecommendationOut(BaseModel):
    id: int
    stock_symbol: str
    stock_name: str
    sector: str
    exchange: str
    trade_horizon: TradeHorizon
    signal: RecommendationSignal
    risk_level: RiskLevel
    confidence_score: float
    current_price: Decimal
    target_price: Optional[Decimal]
    stop_loss: Optional[Decimal]
    upside_potential: Optional[float]
    reason: str
    technical_summary: Optional[str]
    fundamental_summary: Optional[str]
    sentiment_summary: Optional[str]
    portfolio_allocation_pct: Optional[float]
    sector_allocation_pct: Optional[float]
    allocation_warning: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class TodayRecommendations(BaseModel):
    date: str
    buy: list[RecommendationOut]
    add_more: list[RecommendationOut]
    hold: list[RecommendationOut]
    partial_sell: list[RecommendationOut]
    sell: list[RecommendationOut]
    avoid: list[RecommendationOut]
    total_count: int
    last_updated: Optional[datetime]


class MarketOverview(BaseModel):
    nifty50: float
    nifty50_change: float
    nifty50_change_pct: float
    niftybank: float
    niftybank_change: float
    niftybank_change_pct: float
    sensex: float
    sensex_change: float
    sensex_change_pct: float
    nifty_midcap: float
    nifty_midcap_change_pct: float
    market_status: str   # OPEN / CLOSED / PRE_OPEN
    as_of: datetime


class SectorPerformance(BaseModel):
    sector: str
    change_pct: float
    sentiment: str   # BULLISH / BEARISH / NEUTRAL


class NewsItem(BaseModel):
    title: str
    source: str
    url: str
    published_at: str
    sentiment: str   # POSITIVE / NEGATIVE / NEUTRAL
    sentiment_score: float
    stock_symbols: list[str]
    summary: str


class AnalysisRequest(BaseModel):
    symbol: str
    exchange: str = "NSE"
    horizon: TradeHorizon = TradeHorizon.SWING
    force_refresh: bool = False
