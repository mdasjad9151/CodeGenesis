from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from sqlalchemy import text

from api import contest_routes, daily_routes, internal_routes, problem_routes, submission_routes
from core import cache
from db.connection import Database
from db.engine import start_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_database()
    yield
    Database.dispose()


app = FastAPI(title="CodeGenesis problem-service", lifespan=lifespan)
app.include_router(problem_routes.router)
app.include_router(submission_routes.router)
app.include_router(contest_routes.router)
app.include_router(daily_routes.router)
app.include_router(internal_routes.router)


@app.get("/health")
def health(response: Response):
    try:
        with Database.get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        # Redis is optional (cache + rate limits fail open), so it is reported but doesn't fail the check
        return {"status": "ok", "service": "problem-service", "redis": "ok" if cache.ping() else "down"}
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unhealthy", "service": "problem-service"}
