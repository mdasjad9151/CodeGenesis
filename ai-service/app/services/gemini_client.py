"""Google AI Studio (Gemini) client using the google-genai SDK."""
from google import genai
from google.genai import types

from core.configs import ConfigLoader
from schema.generated_problem import GeneratedProblem
from services.prompts import SYSTEM_PROMPT, build_problem_prompt

config = ConfigLoader()


class GeminiNotConfigured(RuntimeError):
    pass


class GeminiClient:
    def __init__(self):
        settings = config.gemini_config()
        if not settings["api_key"]:
            raise GeminiNotConfigured("GEMINI_API_KEY is not set")
        self.model = settings["model"]
        self.client = genai.Client(api_key=settings["api_key"])

    def generate_problem_json(self, topic: str, difficulty: str) -> str:
        """Return Gemini's raw JSON text. Parsing/validation is the caller's job (never trust it)."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=build_problem_prompt(topic, difficulty),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=GeneratedProblem,
                max_output_tokens=8192,
            ),
        )
        if not response.text:
            raise ValueError("Gemini returned an empty response")
        return response.text
