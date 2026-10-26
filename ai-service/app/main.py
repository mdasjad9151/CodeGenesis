from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status

from api import generate_routes
from services.daily_job import create_scheduler
from services.judge0_client import Judge0Client
from services.submission_consumer import SubmissionConsumer

consumer = SubmissionConsumer()
scheduler = create_scheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    consumer.start()
    if scheduler:
        scheduler.start()
    yield
    if scheduler:
        scheduler.shutdown(wait=False)


app = FastAPI(title="CodeGenesis ai-service", lifespan=lifespan)
app.include_router(generate_routes.router)


@app.get("/health")
def health(response: Response):
    consumer_ok = consumer.is_alive()
    if not consumer_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    next_run = scheduler.get_job("daily-challenge").next_run_time if scheduler and scheduler.running else None
    return {
        "status": "ok" if consumer_ok else "unhealthy",
        "service": "ai-service",
        "submission_consumer": "running" if consumer_ok else "down",
        "daily_job_next_run": next_run.isoformat() if next_run else None,
        # Informational: Judge0 runs outside this compose project
        "judge0_reachable": Judge0Client().is_reachable(),
    }
