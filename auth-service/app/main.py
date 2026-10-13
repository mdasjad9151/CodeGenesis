from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from sqlalchemy import text

from api import auth_routes
from db.connection import Database
from db.engine import start_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_database()
    yield
    Database.dispose()


app = FastAPI(title="CodeGenesis auth-service", lifespan=lifespan)
app.include_router(auth_routes.router)


@app.get("/health")
def health(response: Response):
    try:
        with Database.get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "service": "auth-service"}
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unhealthy", "service": "auth-service"}
