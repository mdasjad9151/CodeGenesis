import os
import json
import asyncio
from typing import Any, Dict

import httpx

from .ai_provider import AIProvider


class OpenAIProvider(AIProvider):
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AI_API_KEY")
        self.model = os.getenv("AI_MODEL", "gpt-4o-mini")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY or AI_API_KEY is not set in environment")

    async def _chat(self, messages: list, timeout: int = 60) -> Dict[str, Any]:
        url = f"https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 1500,
        }
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            return r.json()

    async def generate_problem(self, request: Dict[str, Any]) -> Dict[str, Any]:
        system = (
            "You are a problem generator that must output strict JSON matching the schema for CodeGenesis AI-generated problems."
        )
        user = (
            "Generate a programming problem using the following parameters:\n" + json.dumps(request)
        )

        resp = await self._chat([{"role": "system", "content": system}, {"role": "user", "content": user}])
        # best-effort parse JSON block from assistant
        content = ""
        try:
            content = resp["choices"][0]["message"]["content"]
        except Exception:
            raise RuntimeError("Invalid response from AI provider")

        # Attempt to extract JSON substring
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1:
            raise RuntimeError("AI did not return JSON")

        json_text = content[start : end + 1]
        try:
            data = json.loads(json_text)
        except Exception as e:
            raise RuntimeError(f"Failed to parse JSON from AI response: {e}\nContent:\n{content}")

        return data

    async def generate_test_cases(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        # For now, ask the model to propose input generators; actual expected outputs should be produced
        # by running the reference solution. Return structure with `cases` list.
        system = "Generate diverse test case inputs for the following problem in JSON format."
        user = json.dumps(problem)
        resp = await self._chat([{"role": "system", "content": system}, {"role": "user", "content": user}])
        content = resp["choices"][0]["message"]["content"]
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1:
            raise RuntimeError("AI did not return JSON for test cases")
        json_text = content[start : end + 1]
        try:
            data = json.loads(json_text)
        except Exception as e:
            raise RuntimeError(f"Failed to parse JSON from AI response: {e}")
        return data

    async def generate_solution(self, problem: Dict[str, Any], language: str) -> Dict[str, Any]:
        system = "Generate a reference solution for the given problem. Return JSON { 'language': ..., 'code': '...' }"
        user = json.dumps({"problem": problem, "language": language})
        resp = await self._chat([{"role": "system", "content": system}, {"role": "user", "content": user}])
        content = resp["choices"][0]["message"]["content"]
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1:
            raise RuntimeError("AI did not return JSON for solution")
        json_text = content[start : end + 1]
        try:
            data = json.loads(json_text)
        except Exception as e:
            raise RuntimeError(f"Failed to parse JSON from AI response: {e}")
        return data

    async def explain_solution(self, problem: Dict[str, Any], solution: str) -> str:
        system = "Explain the solution and its complexity concisely."
        user = json.dumps({"problem": problem, "solution": solution})
        resp = await self._chat([{"role": "system", "content": system}, {"role": "user", "content": user}])
        return resp["choices"][0]["message"]["content"]

    async def analyze_submission(self, submission: Dict[str, Any]) -> Dict[str, Any]:
        system = "Analyze the submission and return structured analysis."
        user = json.dumps(submission)
        resp = await self._chat([{"role": "system", "content": system}, {"role": "user", "content": user}])
        return {"raw": resp}
