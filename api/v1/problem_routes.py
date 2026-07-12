from fastapi import APIRouter, Cookie, Query

from schema.problem import ProblemDetailResponse, ProblemListResponse
from services.problem_service import ProblemService

router = APIRouter()


@router.get("/api/v1/problems", response_model=ProblemListResponse)
async def get_problem_list(page: int = Query(1, ge=1)):
    problem_service = ProblemService()
    return await problem_service.get_problem_list(page)


@router.get("/api/v1/problems/{problem_id}", response_model=ProblemDetailResponse)
async def get_problem_detail(
    problem_id: int,
    language: str | None = Query(None)
):
    problem_service = ProblemService()
    return await problem_service.get_problem_detail(problem_id, language)
