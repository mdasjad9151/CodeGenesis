from math import ceil

from fastapi import HTTPException, status

from core import cache
from core.configs import ConfigLoader
from repositories.problem_repository import ProblemRepository

config = ConfigLoader()


class ProblemService:
    PAGE_SIZE = 10
    DEFAULT_LANGUAGE = "python"

    def __init__(self):
        self.problem_repository = ProblemRepository()

    def get_problem_list(self, page: int):
        # Cached per page; any create/update/delete bumps the version so stale pages are never served
        cache_key = f"problems:list:v{cache.get_version('problems')}:p{page}"
        cached = cache.get_json(cache_key)
        if cached is not None:
            return cached

        total = self.problem_repository.get_problem_count()
        total_pages = ceil(total / self.PAGE_SIZE) if total else 0
        offset = (page - 1) * self.PAGE_SIZE
        problems = self.problem_repository.get_problem_list(
            limit=self.PAGE_SIZE,
            offset=offset,
        )

        result = {
            "page": page,
            "page_size": self.PAGE_SIZE,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
            "problems": [dict(problem) for problem in problems],
        }
        cache.set_json(cache_key, result, config.redis_config()["problem_list_ttl"])
        return result

    def get_problem_detail(self, problem_id: int, language: str | None = None):
        problem = self.problem_repository.get_problem_by_id(problem_id)
        if not problem:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

        starter_code_map = problem.get("starter_code") or {}
        selected_language = language if language else self.DEFAULT_LANGUAGE
        starter_code = starter_code_map.get(selected_language)

        if starter_code is None:
            selected_language = self.DEFAULT_LANGUAGE
            starter_code = starter_code_map.get(self.DEFAULT_LANGUAGE, "")

        return {
            "problem_id": problem["problem_id"],
            "title": problem["title"],
            "difficulty": problem["difficulty"],
            "description": problem["statement"],
            "input_format": problem["input_format"],
            "output_format": problem["output_format"],
            "constraints": problem.get("constraints") or [],
            "examples": problem.get("examples") or [],
            "sample_testcases": problem.get("sample_testcases") or [],
            "topics": problem.get("topics") or [],
            "hints": problem.get("hints") or [],
            "language": selected_language,
            "starter_code": starter_code,
        }

    @staticmethod
    def _normalize(problem: dict) -> dict:
        # Topics are stored lower-case so topic search/contests can match them exactly
        problem["topics"] = sorted({t.strip().lower() for t in problem.get("topics", []) if t.strip()})
        return problem

    def create_problem(self, problem: dict, created_by: str | None = None):
        problem_id = self.problem_repository.create_problem(self._normalize(problem), created_by)
        cache.bump_version("problems")
        return self.get_problem_detail(problem_id)

    def update_problem(self, problem_id: int, problem: dict):
        if not self.problem_repository.update_problem(problem_id, self._normalize(problem)):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
        cache.bump_version("problems")
        return self.get_problem_detail(problem_id)

    def delete_problem(self, problem_id: int) -> None:
        if not self.problem_repository.delete_problem(problem_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
        cache.bump_version("problems")

    def get_testcases(self, problem_id: int):
        row = self.problem_repository.get_testcases(problem_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")
        return {
            "problem_id": row["problem_id"],
            "testcases": (row["sample_testcases"] or []) + (row["hidden_testcases"] or []),
        }
