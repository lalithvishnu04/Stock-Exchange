from fastapi import APIRouter
from app.core.deps import CurrentUser, DbSession
from app.services.reports import generate_daily_report_for_user
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate/daily")
async def trigger_daily_report(current_user: CurrentUser, db: DbSession):
    html = await generate_daily_report_for_user(db, current_user)
    return {"message": "Daily report generated", "preview_url": f"/reports/preview/daily"}


@router.get("/preview/daily", response_class=HTMLResponse)
async def preview_daily_report(current_user: CurrentUser, db: DbSession):
    html = await generate_daily_report_for_user(db, current_user)
    return HTMLResponse(content=html)
