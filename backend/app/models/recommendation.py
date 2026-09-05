import enum
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Numeric, DateTime, ForeignKey, Enum, func, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class RecommendationSignal(str, enum.Enum):
    BUY = "BUY"
    ADD_MORE = "ADD_MORE"
    HOLD = "HOLD"
    PARTIAL_SELL = "PARTIAL_SELL"
    SELL = "SELL"
    AVOID = "AVOID"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TradeHorizon(str, enum.Enum):
    INTRADAY = "INTRADAY"   # same-day entry/exit
    SWING = "SWING"         # multi-day to multi-week hold
    LONGTERM = "LONGTERM"   # multi-month+ hold, fundamentals-weighted


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    stock_symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    stock_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str] = mapped_column(String(100), nullable=False)
    exchange: Mapped[str] = mapped_column(String(10), default="NSE")

    trade_horizon: Mapped[TradeHorizon] = mapped_column(Enum(TradeHorizon), default=TradeHorizon.SWING, nullable=False)
    signal: Mapped[RecommendationSignal] = mapped_column(Enum(RecommendationSignal), nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)

    # Price context at time of recommendation
    current_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    target_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    stop_loss: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    upside_potential: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # AI reasoning (kept concise for display)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    technical_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    fundamental_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentiment_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Rule enforcement context
    portfolio_allocation_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    sector_allocation_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    allocation_warning: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Performance tracking
    was_correct: Mapped[bool | None] = mapped_column(nullable=True)
    actual_return_pct: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
