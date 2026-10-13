from datetime import date

from fastapi import HTTPException, status

from core import cache
from core.configs import ConfigLoader
from repositories.daily_repository import DailyRepository
from repositories.problem_repository import ProblemRepository

config = ConfigLoader()


class DailyService:
    def __init__(self):
        self.daily_repository = DailyRepository()

    def get_daily(self, challenge_date: date) -> dict:
        cache_key = f"daily:{challenge_date.isoformat()}"
        cached = cache.get_json(cache_key)
        if cached is not None:
            return cached

        rows = self.daily_repository.get_daily(challenge_date)
        result = {"challenge_date": challenge_date.isoformat(), "problems": [dict(row) for row in rows]}
        if result["problems"]:  # don't cache "not generated yet"
            cache.set_json(cache_key, result, config.redis_config()["daily_ttl"])
        return result

    def set_daily(self, request) -> None:
        if not ProblemRepository().get_problem_by_id(request.problem_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
        self.daily_repository.set_daily(request.challenge_date, request.difficulty, request.problem_id, request.topic)
        cache.delete(f"daily:{request.challenge_date.isoformat()}")
