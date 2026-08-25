import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Notification preferences
    telegram_chat_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    telegram_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Zerodha integration (optional)
    zerodha_api_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    zerodha_api_secret: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    zerodha_access_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    zerodha_token_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
