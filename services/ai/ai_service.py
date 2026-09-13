from typing import Dict, Any
from core.configs import ConfigLoader
from .openai_provider import OpenAIProvider


class AIService:
    def __init__(self, provider: str | None = None):
        self.config = ConfigLoader()
        chosen = provider or self.config.__dict__.get("AI_PROVIDER")
        # For now only OpenAIProvider is implemented
        self.provider = OpenAIProvider()

    async def generate_problem(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Validate minimal request
        required = ["difficulty", "topic"]
        for r in required:
            if r not in payload:
                raise ValueError(f"missing required parameter: {r}")

        generated = await self.provider.generate_problem(payload)
        # Basic structural checks
        if not isinstance(generated, dict):
            raise RuntimeError("AI returned invalid problem structure")

        # Ensure required keys exist in generated content
        keys = ["title", "description", "time_limit_ms", "memory_limit_mb", "reference_solution"]
        for k in keys:
            if k not in generated:
                raise RuntimeError(f"AI-generated content missing required key: {k}")

        return generated
