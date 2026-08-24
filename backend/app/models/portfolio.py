from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Numeric, DateTime, ForeignKey, func, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Holding(Base):
    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # From Zerodha
    tradingsymbol: Mapped[str] = mapped_column(String(50), nullable=False)
    exchange: Mapped[str] = mapped_column(String(10), default="NSE")
    isin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    instrument_token: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Stock info
    company_name: Mapped[str] = mapped_column(String(255), default="")
    sector: Mapped[str] = mapped_column(String(100), default="Unknown")
    industry: Mapped[str] = mapped_column(String(100), default="Unknown")

    # Quantities
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    t1_quantity: Mapped[int] = mapped_column(Integer, default=0)  # unsettled

    # Prices
    average_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    last_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    close_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)

    # Computed values (refreshed on sync)
    current_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    invested_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    pnl: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    pnl_pct: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=0)
    day_change: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    day_change_pct: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=0)

    # Portfolio weight (refreshed on sync)
    portfolio_weight_pct: Mapped[float] = mapped_column(Numeric(6, 3), default=0.0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AlertLog(Base):
    __tablename__ = "alert_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)  # telegram, email
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    stock_symbol: Mapped[str | None] = mapped_column(String(20), nullable=True)
    signal: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    report_type: Mapped[str] = mapped_column(String(20), nullable=False)  # daily, weekly
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_html: Mapped[str] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    report_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
