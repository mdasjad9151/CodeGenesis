"""Grades source code against test cases using Judge0. Used by the submission consumer
(and, in Phase 5, to validate AI reference solutions)."""
from services import judge0_client as j0

MAX_ERROR_OUTPUT = 2000


def normalize_output(text: str) -> str:
    """Trim surrounding whitespace and trailing spaces on every line."""
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def _empty_result() -> dict:
    return {
        "status": "completed",
        "verdict": None,
        "passed_count": 0,
        "total_count": 0,
        "runtime_ms": None,
        "memory_kb": None,
        "error_output": None,
    }


def grade(judge: j0.Judge0Client, source_code: str, language: str, testcases: list[dict]) -> dict:
    """Run the code on each test case in order and stop at the first failure (like most judges).

    runtime_ms / memory_kb are the maximum over the test cases that ran.
    """
    result = _empty_result()
    result["total_count"] = len(testcases)
    if not testcases:
        return result | {"status": "failed", "verdict": "Internal Error", "error_output": "Problem has no test cases"}

    for case in testcases:
        run = judge.run(source_code, language, case["input"])

        if run["time_ms"] is not None:
            result["runtime_ms"] = max(result["runtime_ms"] or 0, run["time_ms"])
        if run["memory_kb"] is not None:
            result["memory_kb"] = max(result["memory_kb"] or 0, run["memory_kb"])

        verdict = None
        error_output = None
        if run["status_id"] == j0.STATUS_ACCEPTED:
            if normalize_output(run["stdout"]) != normalize_output(case["output"]):
                verdict = "Wrong Answer"
        elif run["status_id"] == j0.STATUS_TLE:
            verdict = "Time Limit Exceeded"
        elif run["status_id"] == j0.STATUS_COMPILATION_ERROR:
            verdict, error_output = "Compilation Error", run["compile_output"]
        elif run["status_id"] in j0.RUNTIME_ERROR_STATUSES:
            verdict, error_output = "Runtime Error", run["stderr"] or run["status"]
        else:
            # 13 Internal Error, 14 Exec Format Error, or anything unexpected: the judge failed, not the user
            verdict, error_output = "Internal Error", run["message"] or run["status"]

        if verdict:
            result["verdict"] = verdict
            result["error_output"] = (error_output or "")[:MAX_ERROR_OUTPUT] or None
            if verdict == "Internal Error":
                result["status"] = "failed"
            return result

        result["passed_count"] += 1

    result["verdict"] = "Accepted"
    return result
