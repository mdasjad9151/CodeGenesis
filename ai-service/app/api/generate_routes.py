from fastapi import APIRouter, Depends, HTTPException, status

from core.security import require_admin_or_service
from schema.generated_problem import DailyRunResponse, GenerateProblemRequest, GenerateProblemResponse
from services.daily_job import DailyJobAlreadyRunning, run_daily
from services.gemini_client import GeminiClient, GeminiNotConfigured
from services.generation_service import GenerationFailed, generate_validated_problem
from services.judge0_client import Judge0Client
from services.problem_client import ProblemClient

router = APIRouter(dependencies=[Depends(require_admin_or_service)])


@router.post("/generate/problem", response_model=GenerateProblemResponse, status_code=status.HTTP_201_CREATED)
def generate_problem(request: GenerateProblemRequest):
    """Generate -> validate (Pydantic + Judge0) -> save via problem-service. Takes ~10-60s."""
    try:
        payload, attempts = generate_validated_problem(request.topic, request.difficulty, GeminiClient(), Judge0Client())
    except GeminiNotConfigured as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except GenerationFailed as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": "Could not generate a valid problem", "reasons": e.reasons},
        )

    saved = ProblemClient().create_problem(payload)
    return {
        "problem_id": saved["problem_id"],
        "title": saved["title"],
        "topic": request.topic,
        "difficulty": request.difficulty,
        "attempts": attempts,
    }


@router.post("/admin/run-daily", response_model=DailyRunResponse)
def run_daily_now():
    """Run the daily job now (same code the scheduler runs). Already-created difficulties are skipped."""
    try:
        return run_daily()
    except DailyJobAlreadyRunning:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Daily job is already running")
