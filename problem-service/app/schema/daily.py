from datetime import date

from pydantic import BaseModel

from schema.problem import Difficulty


class DailyProblemItem(BaseModel):
    difficulty: Difficulty
    topic: str | None = None
    problem_id: int
    title: str


class DailyChallengeResponse(BaseModel):
    challenge_date: date
    problems: list[DailyProblemItem]


class DailySetRequest(BaseModel):
    """Internal: sent by ai-service's daily job."""
    challenge_date: date
    difficulty: Difficulty
    problem_id: int
    topic: str | None = None
