from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from schema.problem import Difficulty


class ContestGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=50)
    difficulty: Difficulty
    num_questions: int = Field(3, ge=1, le=5)

    @field_validator("topic")
    @classmethod
    def clean_topic(cls, value: str) -> str:
        value = " ".join(value.lower().split())
        if not all(ch.isalnum() or ch in " -+#" for ch in value):
            raise ValueError("topic may only contain letters, digits, spaces and - + #")
        return value


class ContestProblemItem(BaseModel):
    position: int
    problem_id: int
    title: str
    difficulty: str
    solved: bool


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    solved: int


class ContestResponse(BaseModel):
    contest_id: str
    title: str
    topic: str
    difficulty: str
    created_at: datetime
    problems: list[ContestProblemItem]
    my_solved: int
    leaderboard: list[LeaderboardEntry]
    reused_count: int | None = None     # only set by /generate
    generated_count: int | None = None  # only set by /generate
