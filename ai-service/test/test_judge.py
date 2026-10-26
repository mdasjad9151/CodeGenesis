"""Unit tests for the judge pipeline with Judge0 and problem-service mocked.

    docker compose exec ai-service pytest -q /service/test
"""
import base64
import json

import httpx

from services import judge0_client as j0
from services.judge_service import grade, normalize_output
from services.submission_consumer import process_message

TESTCASES = [{"input": "1 2", "output": "3"}, {"input": "5 5", "output": "10"}]


def run_result(status_id, stdout="", **extra):
    return {"status_id": status_id, "status": "x", "stdout": stdout, "stderr": "", "compile_output": "",
            "message": "", "time_ms": 10, "memory_kb": 3000} | extra


class FakeJudge:
    """Returns queued results in order and records the inputs it was asked to run."""
    def __init__(self, *results):
        self.results = list(results)
        self.inputs = []

    def run(self, source_code, language, stdin):
        self.inputs.append(stdin)
        return self.results.pop(0)


def test_normalize_output():
    assert normalize_output("  3  \n") == "3"
    assert normalize_output("1 2   \n3\n\n") == "1 2\n3"
    assert normalize_output("1\r\n2") == "1\n2"


def test_accepted_takes_max_runtime_and_memory():
    judge = FakeJudge(run_result(3, "3\n", time_ms=12, memory_kb=4000), run_result(3, "10", time_ms=30, memory_kb=3500))
    result = grade(judge, "code", "python", TESTCASES)
    assert result["verdict"] == "Accepted"
    assert result["status"] == "completed"
    assert (result["passed_count"], result["total_count"]) == (2, 2)
    assert (result["runtime_ms"], result["memory_kb"]) == (30, 4000)


def test_wrong_answer_stops_early():
    judge = FakeJudge(run_result(3, "4"), run_result(3, "10"))
    result = grade(judge, "code", "python", TESTCASES)
    assert result["verdict"] == "Wrong Answer"
    assert result["passed_count"] == 0
    assert judge.inputs == ["1 2"]


def test_error_verdicts():
    cases = [
        (run_result(5), "Time Limit Exceeded", "completed"),
        (run_result(6, compile_output="error: expected ';'"), "Compilation Error", "completed"),
        (run_result(11, stderr="ZeroDivisionError"), "Runtime Error", "completed"),
        (run_result(13, message="sandbox failure"), "Internal Error", "failed"),
    ]
    for run, verdict, status in cases:
        result = grade(FakeJudge(run), "code", "python", TESTCASES)
        assert (result["verdict"], result["status"]) == (verdict, status)
    assert grade(FakeJudge(cases[1][0]), "c", "cpp", TESTCASES)["error_output"] == "error: expected ';'"


def test_judge0_client_sends_base64_and_limits():
    seen = {}

    def handler(request: httpx.Request):
        seen["params"] = dict(request.url.params)
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={
            "status": {"id": 3, "description": "Accepted"},
            "stdout": base64.b64encode(b"3\n").decode(),
            "time": "0.021", "memory": 3100, "stderr": None, "compile_output": None, "message": None,
        })

    run = j0.Judge0Client(transport=httpx.MockTransport(handler)).run("print(3)", "python", "1 2")
    assert seen["params"] == {"base64_encoded": "true", "wait": "true"}
    assert seen["body"]["language_id"] == 71
    assert base64.b64decode(seen["body"]["source_code"]) == b"print(3)"
    assert base64.b64decode(seen["body"]["stdin"]) == b"1 2"
    assert seen["body"]["cpu_time_limit"] > 0 and seen["body"]["memory_limit"] > 0
    assert run["stdout"] == "3\n" and run["time_ms"] == 21 and run["memory_kb"] == 3100


class FakeProblems:
    def __init__(self, testcases=TESTCASES, fail_fetch=False):
        self.testcases, self.fail_fetch, self.saved = testcases, fail_fetch, []

    def get_testcases(self, problem_id):
        if self.fail_fetch:
            raise httpx.ConnectError("down")
        return self.testcases

    def save_result(self, submission_id, result):
        self.saved.append((submission_id, result))


def message(**overrides):
    return json.dumps({"submission_id": "s1", "problem_id": 1, "language": "python",
                       "source_code": "print(3)"} | overrides).encode()


def test_process_message_marks_running_then_saves_verdict():
    problems = FakeProblems()
    process_message(message(), FakeJudge(run_result(3, "3"), run_result(3, "10")), problems)
    assert problems.saved[0] == ("s1", {"status": "running"})
    assert problems.saved[1][1]["verdict"] == "Accepted"


def test_process_message_reports_internal_error_when_judge_fails():
    problems = FakeProblems(fail_fetch=True)
    process_message(message(), FakeJudge(), problems)
    assert problems.saved[-1][1]["verdict"] == "Internal Error"
    assert problems.saved[-1][1]["status"] == "failed"
