from fastapi import HTTPException, status

from core import cache
from core.configs import ConfigLoader
from core.logging import logger
from repositories.contest_repository import ContestRepository
from repositories.problem_repository import ProblemRepository
from services import ai_client

config = ConfigLoader()


class ContestService:
    def __init__(self):
        self.contest_repository = ContestRepository()
        self.problem_repository = ProblemRepository()

    def generate_contest(self, user: dict, request) -> dict:
        """Instant practice contest: reuse existing problems with this topic/difficulty first,
        and only ask ai-service to generate the missing ones."""
        problem_ids = self.problem_repository.find_problem_ids(request.topic, request.difficulty, request.num_questions)
        reused_count = len(problem_ids)
        missing = request.num_questions - reused_count

        if missing > 0:
            # AI generation costs money/time: limit how often a user can trigger it
            limit = config.ai_service_config()["contest_rate_limit_per_hour"]
            cache.rate_limit("contest-ai", user["id"], limit, 3600)

        for _ in range(missing):
            try:
                problem_ids.append(ai_client.generate_problem(request.topic, request.difficulty))
            except Exception as e:
                # Keep whatever we have; a contest with fewer problems is still useful
                logger.warning(f"AI generation for contest ({request.topic}/{request.difficulty}) failed: {e}")
                break

        if not problem_ids:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="No existing problems for this topic and AI generation failed, try again later",
            )

        title = f"{request.topic.title()} practice ({request.difficulty})"
        contest_id = self.contest_repository.create_contest(
            title, request.topic, request.difficulty, user["id"], problem_ids,
        )
        logger.info(f"Contest {contest_id} created: {reused_count} reused, {len(problem_ids) - reused_count} generated")
        return self.get_contest(user, contest_id) | {
            "reused_count": reused_count,
            "generated_count": len(problem_ids) - reused_count,
        }

    def get_contest(self, user: dict, contest_id: str) -> dict:
        contest = self.contest_repository.get_contest(contest_id)
        if not contest:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")

        solved = self.contest_repository.get_user_solved(contest_id, user["id"])
        problems = [dict(p) | {"solved": p["problem_id"] in solved} for p in self.contest_repository.get_contest_problems(contest_id)]
        leaderboard = [
            {"rank": rank, "user_id": str(row["user_id"]), "solved": row["solved"]}
            for rank, row in enumerate(self.contest_repository.get_scores(contest_id), start=1)
        ]
        return {
            "contest_id": str(contest["contest_id"]),
            "title": contest["title"],
            "topic": contest["topic"],
            "difficulty": contest["difficulty"],
            "created_at": contest["created_at"],
            "problems": problems,
            "my_solved": len(solved),
            "leaderboard": leaderboard,
        }
