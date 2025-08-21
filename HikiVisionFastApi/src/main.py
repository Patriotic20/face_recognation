from fastapi import FastAPI
from core.config import settings
from consumer import lifespan
from fastapi.middleware.cors import CORSMiddleware
from user_logs.api import router as user_logs_router
# from user.api import router as user_router 
# from auth.api import router as auth_router
import uvicorn

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,         
    allow_credentials=True,
    allow_methods=["*"],           
    allow_headers=["*"],           
)

app.include_router(user_logs_router)
# app.include_router(user_router)
# app.include_router(auth_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host=settings.server.host, 
        port=settings.server.port, 
        reload=True
        )
