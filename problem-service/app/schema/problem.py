from typing import Literal

from pydantic import BaseModel, Field

Difficulty = Literal["easy", "medium", "hard"]


class ProblemListItem(BaseModel):
    problem_id: int
    title: str
    difficulty: str


class ProblemListResponse(BaseModel):
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)
    has_next: bool
    has_previous: bool
    problems: list[ProblemListItem]


class ProblemExample(BaseModel):
    input: str
    output: str
    explanation: str | None = None


class ProblemTestcase(BaseModel):
    input: str
    output: str


class ProblemDetailResponse(BaseModel):
    problem_id: int
    title: str
    difficulty: str
    description: str
    input_format: str | None = None
    output_format: str | None = None
    constraints: list[str]
    examples: list[ProblemExample]
    sample_testcases: list[ProblemTestcase]
    topics: list[str]
    hints: list[str]
    language: str
    starter_code: str


class ProblemCreateRequest(BaseModel):
    """Used for both create (POST) and full update (PUT)."""
    title: str = Field(..., min_length=1, max_length=200)
    difficulty: Difficulty
    description: str = Field(..., min_length=1)
    input_format: str | None = None
    output_format: str | None = None
    constraints: list[str] = []
    examples: list[ProblemExample] = []
    sample_testcases: list[ProblemTestcase] = []
    hidden_testcases: list[ProblemTestcase] = Field(..., min_length=1)
    topics: list[str] = []
    hints: list[str] = []
    starter_code: dict[str, str] = {}


class ProblemTestcasesResponse(BaseModel):
    """Internal: everything the judge worker needs to grade a submission."""
    problem_id: int
    testcases: list[ProblemTestcase]
