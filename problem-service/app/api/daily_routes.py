from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from schema.daily import DailyChallengeResponse
from services.daily_service import DailyService

router = APIRouter()


@router.get("/api/v1/daily", response_model=DailyChallengeResponse)
def get_today_daily():
    """Today's (UTC) daily challenge: one problem per difficulty, generated automatically by ai-service."""
    daily_service = DailyService()
    result = daily_service.get_daily(datetime.now(timezone.utc).date())
    if not result["problems"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Today's daily challenge has not been generated yet")
    return result
