"""HTTP client for problem-service's /internal endpoints (authenticated with SERVICE_TOKEN)."""
import httpx

from core.configs import ConfigLoader

config = ConfigLoader()


class ProblemClient:
    def __init__(self, transport: httpx.BaseTransport | None = None):
        settings = config.problem_service_config()
        self.client = httpx.Client(
            base_url=settings["url"],
            headers={"X-Service-Token": settings["service_token"]},
            timeout=10,
            transport=transport,
        )

    def get_testcases(self, problem_id: int) -> list[dict]:
        response = self.client.get(f"/internal/problems/{problem_id}/testcases")
        response.raise_for_status()
        return response.json()["testcases"]

    def save_result(self, submission_id: str, result: dict) -> None:
        response = self.client.put(f"/internal/submissions/{submission_id}/result", json=result)
        response.raise_for_status()

    def create_problem(self, payload: dict) -> dict:
        response = self.client.post("/internal/problems", json=payload)
        response.raise_for_status()
        return response.json()

    def get_daily(self, challenge_date: str) -> dict:
        response = self.client.get(f"/internal/daily/{challenge_date}")
        response.raise_for_status()
        return response.json()

    def set_daily(self, challenge_date: str, difficulty: str, problem_id: int, topic: str) -> None:
        response = self.client.put("/internal/daily", json={
            "challenge_date": challenge_date, "difficulty": difficulty, "problem_id": problem_id, "topic": topic,
        })
        response.raise_for_status()
