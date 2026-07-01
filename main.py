from fastapi import FastAPI
from api.v1.router import router as api_router
from db.engine import start_database
from core.logging import Logger
app = FastAPI()

app.include_router(api_router)

start_database()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)