from fastapi import HTTPException, status

from core import cache
from core.configs import ConfigLoader
from core.logging import logger
from repositories.contest_repository import ContestRepository
from repositories.problem_repository import ProblemRepository
from repositories.submission_repository import SubmissionRepository
from services import queue_publisher

config = ConfigLoader()


class SubmissionService:
    def __init__(self):
        self.submission_repository = SubmissionRepository()
        self.problem_repository = ProblemRepository()

    def create_submission(self, user: dict, request) -> dict:
        settings = config.submission_config()
        cache.rate_limit("submit", user["id"], settings["rate_limit_per_minute"], 60)

        max_code_size = settings["max_code_size"]
        if len(request.source_code.encode()) > max_code_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"source_code is larger than {max_code_size} bytes",
            )

        if not self.problem_repository.get_problem_by_id(request.problem_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

        contest_id = str(request.contest_id) if request.contest_id else None
        if contest_id and not ContestRepository().is_problem_in_contest(contest_id, request.problem_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Problem is not part of this contest")

        submission_id = self.submission_repository.create_submission(
            user_id=user["id"],
            problem_id=request.problem_id,
            language=request.language,
            source_code=request.source_code,
            contest_id=contest_id,
        )

        try:
            queue_publisher.publish_submission({
                "submission_id": submission_id,
                "problem_id": request.problem_id,
                "language": request.language,
                "source_code": request.source_code,
            })
        except Exception as e:
            logger.error(f"Could not publish submission {submission_id}: {e}")
            self.submission_repository.update_result(submission_id, {
                "status": "failed", "verdict": "Internal Error", "passed_count": None, "total_count": None,
                "runtime_ms": None, "memory_kb": None, "error_output": "Judge queue unavailable",
            })
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Judge queue unavailable, try again")

        logger.info(f"Submission {submission_id} queued for problem {request.problem_id}")
        return {"submission_id": submission_id, "status": "queued"}

    def get_submission(self, user: dict, submission_id: str) -> dict:
        submission = self.submission_repository.get_submission(submission_id)
        # Users only see their own submissions; 404 (not 403) so ids can't be probed
        if not submission or (str(submission["user_id"]) != user["id"] and user["role"] != "admin"):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
        return dict(submission) | {
            "submission_id": str(submission["submission_id"]),
            "contest_id": str(submission["contest_id"]) if submission["contest_id"] else None,
        }

    def save_result(self, submission_id: str, result: dict) -> None:
        if not self.submission_repository.update_result(submission_id, result):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
        logger.info(f"Submission {submission_id} -> {result['status']} / {result.get('verdict')}")
