"""Daily challenge job: 1 problem per difficulty on a rotating topic, fully automatic.

Scheduled with APScheduler inside ai-service, and also callable via POST /admin/run-daily.
Safe to re-run: difficulties that already have a daily problem for today are skipped.
"""
import threading
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from core.configs import ConfigLoader
from core.logging import logger
from services.gemini_client import GeminiClient
from services.generation_service import GenerationFailed, generate_validated_problem
from services.judge0_client import Judge0Client
from services.problem_client import ProblemClient

config = ConfigLoader()
DIFFICULTIES = ["easy", "medium", "hard"]
_run_lock = threading.Lock()


class DailyJobAlreadyRunning(Exception):
    pass


def topic_for(day) -> str:
    topics = config.daily_config()["topics"]
    return topics[day.toordinal() % len(topics)]


def run_daily(gemini=None, judge=None, problems=None, today=None) -> dict:
    if not _run_lock.acquire(blocking=False):
        raise DailyJobAlreadyRunning()
    try:
        today = today or datetime.now(timezone.utc).date()
        topic = topic_for(today)
        problems = problems or ProblemClient()
        existing = {p["difficulty"] for p in problems.get_daily(today.isoformat())["problems"]}
        logger.info(f"Daily job for {today}: topic '{topic}', already done: {sorted(existing) or 'none'}")

        results = []
        for difficulty in DIFFICULTIES:
            if difficulty in existing:
                results.append({"difficulty": difficulty, "status": "skipped", "detail": "already exists"})
                continue
            try:
                gemini = gemini or GeminiClient()
                judge = judge or Judge0Client()
                payload, attempts = generate_validated_problem(topic, difficulty, gemini, judge)
                problem_id = problems.create_problem(payload)["problem_id"]
                problems.set_daily(today.isoformat(), difficulty, problem_id, topic)
                results.append({"difficulty": difficulty, "status": "created", "problem_id": problem_id,
                                "detail": f"validated in {attempts} attempt(s)"})
            except GenerationFailed as e:
                results.append({"difficulty": difficulty, "status": "failed", "detail": str(e)})
            except Exception as e:
                logger.error(f"Daily job {difficulty} failed: {e}")
                results.append({"difficulty": difficulty, "status": "failed", "detail": f"{type(e).__name__}: {e}"})

        logger.info(f"Daily job for {today} finished: {[(r['difficulty'], r['status']) for r in results]}")
        return {"challenge_date": today.isoformat(), "topic": topic, "results": results}
    finally:
        _run_lock.release()


def _scheduled_run() -> None:
    try:
        run_daily()
    except DailyJobAlreadyRunning:
        logger.warning("Daily job skipped: a run is already in progress")
    except Exception as e:
        logger.error(f"Daily job crashed: {e}")


def create_scheduler() -> BackgroundScheduler | None:
    settings = config.daily_config()
    if not settings["enabled"]:
        logger.info("Daily job disabled (DAILY_JOB_ENABLED=false)")
        return None
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        _scheduled_run,
        CronTrigger(hour=settings["hour_utc"], minute=0, timezone="UTC"),
        id="daily-challenge",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    return scheduler
