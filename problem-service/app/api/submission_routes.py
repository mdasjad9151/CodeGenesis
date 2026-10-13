from uuid import UUID

from fastapi import APIRouter, Depends, status

from core.security import get_current_user
from schema.submission import SubmissionCreatedResponse, SubmissionCreateRequest, SubmissionResponse
from services.submission_service import SubmissionService

router = APIRouter()


@router.post(
    "/api/v1/submissions",
    response_model=SubmissionCreatedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_submission(request: SubmissionCreateRequest, current_user=Depends(get_current_user)):
    submission_service = SubmissionService()
    return submission_service.create_submission(current_user, request)


@router.get("/api/v1/submissions/{submission_id}", response_model=SubmissionResponse)
def get_submission(submission_id: UUID, current_user=Depends(get_current_user)):
    submission_service = SubmissionService()
    return submission_service.get_submission(current_user, str(submission_id))
