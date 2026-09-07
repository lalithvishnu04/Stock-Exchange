"""APScheduler-based background job runner."""
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

IST = pytz.timezone("Asia/Kolkata")


def setup_scheduler(app) -> AsyncIOScheduler:
    from app.config import settings

    scheduler = AsyncIOScheduler(timezone=IST)

    pre_h, pre_m = settings.PRE_MARKET_ANALYSIS_TIME.split(":")
    post_h, post_m = settings.POST_MARKET_ANALYSIS_TIME.split(":")
    report_h, report_m = settings.DAILY_REPORT_TIME.split(":")

    # Pre-market: weekdays 8 AM IST
    scheduler.add_job(
        _run_pre_market_analysis,
        CronTrigger(day_of_week="mon-fri", hour=int(pre_h), minute=int(pre_m), timezone=IST),
        id="pre_market",
        replace_existing=True,
    )

    # Intraday: weekdays every N minutes during market hours 9:15–15:30
    scheduler.add_job(
        _run_intraday_analysis,
        CronTrigger(
            day_of_week="mon-fri",
            hour="9-15",
            minute=f"*/{settings.INTRADAY_INTERVAL_MINUTES}",
            timezone=IST,
        ),
        id="intraday",
        replace_existing=True,
    )

    # Post-market: weekdays 4 PM IST
    scheduler.add_job(
        _run_post_market_analysis,
        CronTrigger(day_of_week="mon-fri", hour=int(post_h), minute=int(post_m), timezone=IST),
        id="post_market",
        replace_existing=True,
    )

    # Daily report: weekdays 5 PM IST
    scheduler.add_job(
        _run_daily_report,
        CronTrigger(day_of_week="mon-fri", hour=int(report_h), minute=int(report_m), timezone=IST),
        id="daily_report",
        replace_existing=True,
    )

    # Weekly report: Friday 5 PM IST
    scheduler.add_job(
        _run_weekly_report,
        CronTrigger(day_of_week="fri", hour=int(report_h), minute=int(report_m), timezone=IST),
        id="weekly_report",
        replace_existing=True,
    )

    # Market-wide scan (full stock universe, excluding each user's holdings) —
    # populates /market-picks. Runs 30 min after pre-market holdings analysis so
    # it doesn't compete with it on the single worker.
    scan_time = (datetime(2000, 1, 1, int(pre_h), int(pre_m)) + timedelta(minutes=30)).time()
    scheduler.add_job(
        _run_market_scan_swing_longterm,
        CronTrigger(day_of_week="mon-fri", hour=scan_time.hour, minute=scan_time.minute, timezone=IST),
        id="market_scan_daily",
        replace_existing=True,
    )

    # Intraday market scan — once shortly after market open (not every N
    # minutes like the holdings check; scanning ~190 symbols that often would
    # be too heavy for a free yfinance-based pipeline).
    scheduler.add_job(
        _run_market_scan_intraday,
        CronTrigger(day_of_week="mon-fri", hour=9, minute=45, timezone=IST),
        id="market_scan_intraday",
        replace_existing=True,
    )

    return scheduler


async def _run_pre_market_analysis():
    """Analyse all user holdings before market opens."""
    from app.services.analysis_runner import run_full_analysis_for_all_users, refresh_holdings_for_all_users
    await refresh_holdings_for_all_users()
    await run_full_analysis_for_all_users(session_type="pre_market")


async def _run_intraday_analysis():
    """Light intraday check – refresh holding prices and look for stop-loss breaches."""
    from app.services.analysis_runner import run_intraday_check_for_all_users, refresh_holdings_for_all_users
    await refresh_holdings_for_all_users()
    await run_intraday_check_for_all_users()


async def _run_post_market_analysis():
    """Full post-market analysis and alert generation."""
    from app.services.analysis_runner import run_full_analysis_for_all_users, refresh_holdings_for_all_users
    await refresh_holdings_for_all_users()
    await run_full_analysis_for_all_users(session_type="post_market")


async def _run_daily_report():
    from app.services.reports import generate_daily_reports_for_all_users
    await generate_daily_reports_for_all_users()


async def _run_weekly_report():
    from app.services.reports import generate_weekly_reports_for_all_users
    await generate_weekly_reports_for_all_users()


async def _run_market_scan_swing_longterm():
    """Scan the full stock universe for SWING and LONG-TERM 'new buy' candidates."""
    from app.services.analysis_runner import run_market_scan_for_all_users
    await run_market_scan_for_all_users("SWING", full_universe=True)
    await run_market_scan_for_all_users("LONGTERM", full_universe=True)


async def _run_market_scan_intraday():
    """Scan the full stock universe for INTRADAY 'new buy' candidates."""
    from app.services.analysis_runner import run_market_scan_for_all_users
    await run_market_scan_for_all_users("INTRADAY", full_universe=True)
