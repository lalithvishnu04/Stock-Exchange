import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import redis.asyncio as aioredis

from app.config import settings
from app.database import create_tables
from app.routers import auth, portfolio, recommendations, reports
from app.services.scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler
    logger.info("Starting Stock Market Advisor API...")
    await create_tables()

    # Verify Redis connectivity
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        await redis_client.ping()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning(f"Redis unavailable: {e}")
    finally:
        await redis_client.aclose()

    # Start scheduler
    _scheduler = setup_scheduler(app)
    _scheduler.start()
    logger.info("Scheduler started with %d jobs", len(_scheduler.get_jobs()))

    yield

    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
    logger.info("Shutdown complete")


app = FastAPI(
    title="Stock Market Advisor API",
    description="AI-powered Indian stock market advisor. Connects to Zerodha, analyzes markets, and provides BUY/HOLD/SELL recommendations.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(auth.router, prefix="/api")
app.include_router(portfolio.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": settings.APP_NAME}
