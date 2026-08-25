from fastapi import APIRouter, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy import select
from app.core.deps import DbSession
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.models.recommendation import Recommendation
from app.schemas.auth import UserCreate, UserLogin, TokenResponse, RefreshTokenRequest, UserOut, UserSettingsUpdate, ZerodhaConnectRequest
from app.core.deps import CurrentUser
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: DbSession):
    existing = (await db.execute(select(User).where(
        (User.username == payload.username) | (User.email == payload.email)
    ))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name or "",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return _user_out(user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: DbSession):
    user = (await db.execute(select(User).where(User.username == payload.username))).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshTokenRequest, db: DbSession):
    data = decode_token(payload.refresh_token)
    if not data or data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = (await db.execute(select(User).where(User.id == int(data["sub"])))).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: CurrentUser):
    return _user_out(current_user)


@router.put("/settings", response_model=UserOut)
async def update_settings(payload: UserSettingsUpdate, current_user: CurrentUser, db: DbSession):
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.email_alerts_enabled is not None:
        current_user.email_alerts_enabled = payload.email_alerts_enabled
    if payload.telegram_alerts_enabled is not None:
        current_user.telegram_alerts_enabled = payload.telegram_alerts_enabled
    if payload.telegram_chat_id is not None:
        current_user.telegram_chat_id = payload.telegram_chat_id
    if payload.zerodha_api_key is not None:
        current_user.zerodha_api_key = payload.zerodha_api_key or None
    if payload.zerodha_api_secret is not None:
        current_user.zerodha_api_secret = payload.zerodha_api_secret or None
    await db.flush()
    await db.refresh(current_user)
    return _user_out(current_user)


@router.post("/zerodha/connect")
async def connect_zerodha(payload: ZerodhaConnectRequest, current_user: CurrentUser, db: DbSession):
    if not current_user.zerodha_api_key or not current_user.zerodha_api_secret:
        raise HTTPException(status_code=400, detail="Save Zerodha API key and secret first via /auth/settings")

    from app.services.zerodha import ZerodhaService
    from datetime import datetime, timezone, timedelta
    svc = ZerodhaService(current_user.zerodha_api_key, current_user.zerodha_api_secret)
    try:
        session_data = svc.generate_session(payload.request_token)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Zerodha auth failed: {exc}")

    current_user.zerodha_access_token = session_data["access_token"]
    current_user.zerodha_token_expiry = datetime.now(timezone.utc) + timedelta(hours=18)
    await db.flush()
    return {"message": "Zerodha connected successfully", "user": session_data.get("user_name")}


def _user_out(user: User) -> dict:
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        email_alerts_enabled=user.email_alerts_enabled,
        telegram_alerts_enabled=user.telegram_alerts_enabled,
        has_zerodha_connected=bool(user.zerodha_access_token),
        created_at=user.created_at,
    )
