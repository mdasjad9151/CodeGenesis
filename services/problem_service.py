from math import ceil

from fastapi import HTTPException

from repositories.problem_repository import ProblemRepository


class ProblemService:
    PAGE_SIZE = 10
    DEFAULT_LANGUAGE = "python"

    def __init__(self):
        self.problem_repository = ProblemRepository()

    async def get_problem_list(self, page: int):
        total = self.problem_repository.get_problem_count()
        total_pages = ceil(total / self.PAGE_SIZE) if total else 0
        offset = (page - 1) * self.PAGE_SIZE
        problems = self.problem_repository.get_problem_list(
            limit=self.PAGE_SIZE,
            offset=offset,
        )

        return {
            "page": page,
            "page_size": self.PAGE_SIZE,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
            "problems": [dict(problem) for problem in problems],
        }

    async def get_problem_detail(self, problem_id: int, language: str | None = None):
        problem = self.problem_repository.get_problem_by_id(problem_id)
        if not problem:
            raise HTTPException(status_code=404, detail="Problem not found")

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
            "examples": problem.get("examples") or [],
            "sample_testcases": problem.get("sample_testcases") or [],
            "topics": problem.get("topics") or [],
            "language": selected_language,
            "starter_code": starter_code,
        }
