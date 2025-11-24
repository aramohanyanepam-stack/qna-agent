from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.api.v1 import routes as api_v1
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    application = FastAPI(title="QNA-Agent", lifespan=lifespan)

    application.include_router(api_v1.router, prefix="/api/v1/chat")

    return application


app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8085, reload=True)
