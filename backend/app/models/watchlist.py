"""Watchlist model – tracks stocks user wants to buy."""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Numeric, DateTime, ForeignKey, func, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Watchlist(Base):
    __tablename__ = "watchlist"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    stock_symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    stock_name: Mapped[str] = mapped_column(String(255), nullable=False)
    exchange: Mapped[str] = mapped_column(String(10), default="NSE")
    
    # Recommendation context at time of adding
    signal: Mapped[str] = mapped_column(String(20), nullable=False)  # BUY, ADD_MORE, SELL
    confidence_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)
    current_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    target_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    
    # Tracking
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    bought_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_bought: Mapped[bool] = mapped_column(default=False)
    
    class Config:
        from_attributes = True
