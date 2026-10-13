from dotenv import load_dotenv
import os
load_dotenv()
class ConfigLoader:
    def __init__(self, config_path: str =None):
        self.config_path = config_path

    def get_db_config(self):
        return {
            'postgre_uri': os.getenv('POSTGRESQL_URI'),
        }

    def jwt_config(self):
        return {
            "secret_key": os.getenv('JWT_SECRET_KEY'),
            'algorithm': os.getenv('JWT_ALGORITHM', 'HS256'),
        }

    def rabbitmq_config(self):
        return {
            "url": os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/"),
            "submission_queue": "submissions",
        }

    def service_token(self):
        return os.getenv("SERVICE_TOKEN", "")

    def submission_config(self):
        return {
            "max_code_size": int(os.getenv("MAX_CODE_SIZE", "65536")),
            "languages": ["python", "cpp", "java", "javascript"],
            "rate_limit_per_minute": int(os.getenv("SUBMISSION_RATE_LIMIT_PER_MINUTE", "10")),
        }

    def redis_config(self):
        return {
            "url": os.getenv("REDIS_URL", "redis://redis:6379/0"),
            "problem_list_ttl": 60,
            "daily_ttl": 300,
        }

    def ai_service_config(self):
        return {
            "url": os.getenv("AI_SERVICE_URL", "http://ai-service:8003").rstrip("/"),
            # One AI generation can take up to ~1 min per attempt (3 attempts max)
            "timeout_seconds": float(os.getenv("AI_SERVICE_TIMEOUT_SECONDS", "240")),
            # Contests that need AI generation, per user per hour
            "contest_rate_limit_per_hour": int(os.getenv("AI_GENERATION_RATE_LIMIT", "10")),
        }
