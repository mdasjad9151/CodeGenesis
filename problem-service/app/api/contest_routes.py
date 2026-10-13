from uuid import UUID

from fastapi import APIRouter, Depends, status

from core.security import get_current_user
from schema.contest import ContestGenerateRequest, ContestResponse
from services.contest_service import ContestService

router = APIRouter()


@router.post("/api/v1/contests/generate", response_model=ContestResponse, status_code=status.HTTP_201_CREATED)
def generate_contest(request: ContestGenerateRequest, current_user=Depends(get_current_user)):
    """Instant when enough problems exist for the topic; otherwise waits for ai-service to generate the rest."""
    contest_service = ContestService()
    return contest_service.generate_contest(current_user, request)


@router.get("/api/v1/contests/{contest_id}", response_model=ContestResponse)
def get_contest(contest_id: UUID, current_user=Depends(get_current_user)):
    contest_service = ContestService()
    return contest_service.get_contest(current_user, str(contest_id))
