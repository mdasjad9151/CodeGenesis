"""HTTP client for ai-service (authenticated with SERVICE_TOKEN)."""
import httpx

from core.configs import ConfigLoader

config = ConfigLoader()


def generate_problem(topic: str, difficulty: str) -> int:
    """Ask ai-service for a new Judge0-validated problem; it saves it here via /internal/problems. Returns problem_id."""
    settings = config.ai_service_config()
    response = httpx.post(
        f"{settings['url']}/generate/problem",
        json={"topic": topic, "difficulty": difficulty},
        headers={"X-Service-Token": config.service_token()},
        timeout=settings["timeout_seconds"],
    )
    response.raise_for_status()
    return response.json()["problem_id"]
