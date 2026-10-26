"""Generate a problem with Gemini, validate it with Pydantic + Judge0, then save it via problem-service.

A problem is only saved if its Python reference solution passes every example and test case in Judge0.
Otherwise we regenerate, up to AI_MAX_GENERATION_ATTEMPTS times.
"""
from pydantic import ValidationError

from core.configs import ConfigLoader
from core.logging import logger
from schema.generated_problem import GeneratedProblem
from services.judge_service import grade

config = ConfigLoader()


class JudgeUnavailable(Exception):
    """Judge0 itself failed: retrying generation would only waste Gemini calls."""


class GenerationFailed(Exception):
    def __init__(self, reasons: list[str]):
        self.reasons = reasons
        super().__init__("; ".join(reasons))


def validate_with_judge0(problem: GeneratedProblem, judge) -> str | None:
    """Run the reference solution on examples + test cases. Returns None if all pass, else a reason."""
    cases = [{"input": e.input, "output": e.output} for e in problem.examples]
    cases += [{"input": t.input, "output": t.expected_output} for t in problem.test_cases]
    result = grade(judge, problem.reference_solution, "python", cases)
    if result["verdict"] == "Internal Error":
        raise JudgeUnavailable(f"Judge0 internal error: {result['error_output']}")
    if result["verdict"] == "Accepted":
        return None
    return f"reference solution got {result['verdict']} ({result['passed_count']}/{result['total_count']} passed)"


def to_problem_payload(problem: GeneratedProblem, topic: str, difficulty: str) -> dict:
    """Map the AI format to problem-service's ProblemCreateRequest."""
    return {
        "title": problem.title,
        "difficulty": difficulty,
        "description": problem.description,
        "input_format": problem.input_format,
        "output_format": problem.output_format,
        "constraints": problem.constraints,
        "examples": [e.model_dump() for e in problem.examples],
        "sample_testcases": [{"input": e.input, "output": e.output} for e in problem.examples],
        "hidden_testcases": [{"input": t.input, "output": t.expected_output} for t in problem.test_cases],
        "topics": [topic],
        "hints": problem.hints,
        "starter_code": {},
    }


def generate_validated_problem(topic: str, difficulty: str, gemini, judge) -> tuple[dict, int]:
    """Returns (problem-service payload, attempts used). Raises GenerationFailed."""
    max_attempts = config.gemini_config()["max_attempts"]
    reasons = []

    for attempt in range(1, max_attempts + 1):
        try:
            raw = gemini.generate_problem_json(topic, difficulty)
            problem = GeneratedProblem.model_validate_json(raw)
            failure = validate_with_judge0(problem, judge)
        except JudgeUnavailable as e:
            raise GenerationFailed(reasons + [f"attempt {attempt}: {e}"]) from e
        except ValidationError as e:
            failure = f"invalid JSON from model: {e.error_count()} error(s), first: {e.errors()[0]['msg']}"
        except Exception as e:
            failure = f"{type(e).__name__}: {e}"

        if failure is None:
            logger.info(f"Generated '{problem.title}' ({difficulty}, {topic}) on attempt {attempt}")
            return to_problem_payload(problem, topic, difficulty), attempt

        logger.warning(f"Attempt {attempt}/{max_attempts} for {difficulty} '{topic}' discarded: {failure}")
        reasons.append(f"attempt {attempt}: {failure}")

    raise GenerationFailed(reasons)
