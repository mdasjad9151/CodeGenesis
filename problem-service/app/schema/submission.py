from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

Language = Literal["python", "cpp", "java", "javascript"]
SubmissionStatus = Literal["queued", "running", "completed", "failed"]
Verdict = Literal[
    "Accepted",
    "Wrong Answer",
    "Time Limit Exceeded",
    "Runtime Error",
    "Compilation Error",
    "Internal Error",
]


class SubmissionCreateRequest(BaseModel):
    problem_id: int
    language: Language
    source_code: str = Field(..., min_length=1)
    contest_id: UUID | None = None  # set when submitting inside a contest (counts towards its score)


class SubmissionCreatedResponse(BaseModel):
    submission_id: str
    status: SubmissionStatus


class SubmissionResponse(BaseModel):
    submission_id: str
    problem_id: int
    contest_id: str | None = None
    language: str
    status: SubmissionStatus
    verdict: Verdict | None = None
    passed_count: int | None = None
    total_count: int | None = None
    runtime_ms: int | None = None
    memory_kb: int | None = None
    error_output: str | None = None
    created_at: datetime


class SubmissionResultRequest(BaseModel):
    """Internal: sent by the judge worker (ai-service)."""
    status: SubmissionStatus
    verdict: Verdict | None = None
    passed_count: int | None = Field(None, ge=0)
    total_count: int | None = Field(None, ge=0)
    runtime_ms: int | None = Field(None, ge=0)
    memory_kb: int | None = Field(None, ge=0)
    error_output: str | None = None
