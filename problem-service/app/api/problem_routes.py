from fastapi import APIRouter, Depends, Query, Response, status

from core.security import require_admin
from schema.problem import ProblemCreateRequest, ProblemDetailResponse, ProblemListResponse
from services.problem_service import ProblemService

router = APIRouter()


@router.get("/api/v1/problems", response_model=ProblemListResponse)
def get_problem_list(page: int = Query(1, ge=1)):
    problem_service = ProblemService()
    return problem_service.get_problem_list(page)


@router.get("/api/v1/problems/{problem_id}", response_model=ProblemDetailResponse)
def get_problem_detail(
    problem_id: int,
    language: str | None = Query(None)
):
    problem_service = ProblemService()
    return problem_service.get_problem_detail(problem_id, language)


@router.post("/api/v1/problems", response_model=ProblemDetailResponse, status_code=status.HTTP_201_CREATED)
def create_problem(request: ProblemCreateRequest, admin=Depends(require_admin)):
    problem_service = ProblemService()
    return problem_service.create_problem(request.model_dump(), created_by=admin["id"])


@router.put("/api/v1/problems/{problem_id}", response_model=ProblemDetailResponse)
def update_problem(problem_id: int, request: ProblemCreateRequest, admin=Depends(require_admin)):
    problem_service = ProblemService()
    return problem_service.update_problem(problem_id, request.model_dump())


@router.delete("/api/v1/problems/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_problem(problem_id: int, admin=Depends(require_admin)):
    problem_service = ProblemService()
    problem_service.delete_problem(problem_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
