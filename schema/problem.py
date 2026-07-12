from pydantic import BaseModel, Field


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


class ProblemSampleTestcase(BaseModel):
    input: str
    output: str


class ProblemDetailResponse(BaseModel):
    problem_id: int
    title: str
    difficulty: str
    description: str
    input_format: str | None = None
    output_format: str | None = None
    examples: list[ProblemExample]
    sample_testcases: list[ProblemSampleTestcase]
    topics: list[str]
    language: str
    starter_code: str
