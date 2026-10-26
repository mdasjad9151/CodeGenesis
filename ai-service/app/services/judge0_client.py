"""Thin client for a self-hosted Judge0. All untrusted code (user or AI) runs only through here."""
import base64

import httpx

from core.configs import LANGUAGES, ConfigLoader

config = ConfigLoader()

# Judge0 status ids: https://github.com/judge0/judge0/blob/master/docs/api/statuses.md
STATUS_ACCEPTED = 3
STATUS_TLE = 5
STATUS_COMPILATION_ERROR = 6
RUNTIME_ERROR_STATUSES = {7, 8, 9, 10, 11, 12}  # SIGSEGV, SIGXFSZ, SIGFPE, SIGABRT, NZEC, Other


def _b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


def _unb64(value: str | None) -> str:
    if not value:
        return ""
    return base64.b64decode(value).decode(errors="replace")


class Judge0Client:
    def __init__(self, transport: httpx.BaseTransport | None = None):
        self.settings = config.judge0_config()
        headers = {"X-Auth-Token": self.settings["auth_token"]} if self.settings["auth_token"] else {}
        self.client = httpx.Client(
            base_url=self.settings["url"],
            headers=headers,
            timeout=self.settings["timeout_seconds"],
            transport=transport,
        )

    def run(self, source_code: str, language: str, stdin: str) -> dict:
        """Run one program on one input and wait for the result.

        Returns {status_id, status, stdout, stderr, compile_output, time_ms, memory_kb}.
        """
        if language not in LANGUAGES:
            raise ValueError(f"Unsupported language: {language}")

        payload = {
            "source_code": _b64(source_code),
            "language_id": LANGUAGES[language],
            "stdin": _b64(stdin),
            "cpu_time_limit": self.settings["cpu_time_limit"],
            "wall_time_limit": self.settings["cpu_time_limit"] * 3,
            "memory_limit": self.settings["memory_limit_kb"],
        }
        response = self.client.post("/submissions", params={"base64_encoded": "true", "wait": "true"}, json=payload)
        response.raise_for_status()
        data = response.json()

        return {
            "status_id": data["status"]["id"],
            "status": data["status"]["description"],
            "stdout": _unb64(data.get("stdout")),
            "stderr": _unb64(data.get("stderr")),
            "compile_output": _unb64(data.get("compile_output")),
            "message": _unb64(data.get("message")),
            "time_ms": int(float(data["time"]) * 1000) if data.get("time") else None,
            "memory_kb": data.get("memory"),
        }

    def is_reachable(self) -> bool:
        try:
            return self.client.get("/about", timeout=3).status_code == 200
        except httpx.HTTPError:
            return False
