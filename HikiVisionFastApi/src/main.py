from fastapi import FastAPI
from core.config import settings
from consumer import lifespan
from user_logs.api import router as user_logs_router
import uvicorn

app = FastAPI(lifespan=lifespan)


app.include_router(user_logs_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host=settings.server.host, 
        port=settings.server.port, 
        reload=True
        )
