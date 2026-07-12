from fastapi import FastAPI

from api.v1 import auth_routes, problem_routes, router
from db.engine import start_database
from core.logging import Logger

app = FastAPI()

# app.include_router(router.router)
app.include_router(auth_routes.router)
app.include_router(problem_routes.router)

start_database()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=3000, reload=True)
