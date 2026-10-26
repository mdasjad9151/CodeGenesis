from dotenv import load_dotenv
import os
load_dotenv()

# Judge0 language ids (checked against GET /languages on Judge0 1.13.1)
LANGUAGES = {
    "python": 71,      # Python (3.8.1)
    "cpp": 54,         # C++ (GCC 9.2.0)
    "java": 62,        # Java (OpenJDK 13.0.1) - class must be named Main
    "javascript": 63,  # JavaScript (Node.js 12.14.0)
}


class ConfigLoader:
    def __init__(self, config_path: str =None):
        self.config_path = config_path

    def judge0_config(self):
        return {
            "url": os.getenv("JUDGE0_URL", "http://host.docker.internal:2358").rstrip("/"),
            "auth_token": os.getenv("JUDGE0_AUTH_TOKEN", ""),
            # Per test case limits sent to Judge0
            "cpu_time_limit": int(os.getenv("DEFAULT_TIME_LIMIT_MS", "2000")) / 1000,
            "memory_limit_kb": int(os.getenv("DEFAULT_MEMORY_LIMIT_MB", "256")) * 1024,
            # Global HTTP timeout for one Judge0 call (wait=true blocks until the run finishes)
            "timeout_seconds": float(os.getenv("JUDGE0_TIMEOUT_SECONDS", "30")),
        }

    def rabbitmq_config(self):
        return {
            "url": os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/"),
            "submission_queue": "submissions",
        }

    def jwt_config(self):
        return {
            "secret_key": os.getenv('JWT_SECRET_KEY'),
            'algorithm': os.getenv('JWT_ALGORITHM', 'HS256'),
        }

    def service_token(self):
        return os.getenv("SERVICE_TOKEN", "")

    def gemini_config(self):
        return {
            "api_key": os.getenv("GEMINI_API_KEY", ""),
            "model": os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
            "max_attempts": int(os.getenv("AI_MAX_GENERATION_ATTEMPTS", "3")),
        }

    def daily_config(self):
        topics = os.getenv(
            "DAILY_TOPICS",
            "arrays,strings,hashing,two pointers,stack,binary search,sorting,greedy,dynamic programming,math",
        )
        return {
            "topics": [t.strip().lower() for t in topics.split(",") if t.strip()],
            # Runs once a day at this UTC hour
            "hour_utc": int(os.getenv("DAILY_JOB_HOUR_UTC", "0")),
            "enabled": os.getenv("DAILY_JOB_ENABLED", "true").lower() == "true",
        }

    def problem_service_config(self):
        return {
            "url": os.getenv("PROBLEM_SERVICE_URL", "http://problem-service:8002").rstrip("/"),
            "service_token": os.getenv("SERVICE_TOKEN", ""),
        }
