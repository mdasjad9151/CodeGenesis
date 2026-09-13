from typing import Any, Dict


class AIProvider:
    async def generate_problem(self, request: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError()

    async def generate_test_cases(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError()

    async def generate_solution(self, problem: Dict[str, Any], language: str) -> Dict[str, Any]:
        raise NotImplementedError()

    async def explain_solution(self, problem: Dict[str, Any], solution: str) -> str:
        raise NotImplementedError()

    async def analyze_submission(self, submission: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError()
