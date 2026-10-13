"""Endpoints for other services only (ai-service). Protected by the X-Service-Token header."""
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from core.security import require_service_token
from schema.daily import DailyChallengeResponse, DailySetRequest
from schema.problem import ProblemCreateRequest, ProblemDetailResponse, ProblemTestcasesResponse
from schema.submission import SubmissionResultRequest
from services.daily_service import DailyService
from services.problem_service import ProblemService
from services.submission_service import SubmissionService

router = APIRouter(prefix="/internal", tags=["internal"], dependencies=[Depends(require_service_token)])


@router.post("/problems", response_model=ProblemDetailResponse, status_code=status.HTTP_201_CREATED)
def create_problem(request: ProblemCreateRequest):
    """Used by ai-service to store AI-generated (already Judge0-validated) problems."""
    problem_service = ProblemService()
    return problem_service.create_problem(request.model_dump())


@router.get("/problems/{problem_id}/testcases", response_model=ProblemTestcasesResponse)
def get_problem_testcases(problem_id: int):
    problem_service = ProblemService()
    return problem_service.get_testcases(problem_id)


@router.put("/submissions/{submission_id}/result", status_code=status.HTTP_204_NO_CONTENT)
def save_submission_result(submission_id: UUID, request: SubmissionResultRequest):
    submission_service = SubmissionService()
    submission_service.save_result(str(submission_id), request.model_dump())
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/daily/{challenge_date}", response_model=DailyChallengeResponse)
def get_daily(challenge_date: date):
    daily_service = DailyService()
    return daily_service.get_daily(challenge_date)


@router.put("/daily", status_code=status.HTTP_204_NO_CONTENT)
def set_daily(request: DailySetRequest):
    daily_service = DailyService()
    daily_service.set_daily(request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
