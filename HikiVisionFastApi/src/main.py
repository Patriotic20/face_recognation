from fastapi import FastAPI
from core.config import settings
from consumer import lifespan
from router import router as api_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI(lifespan=lifespan)

app.mount("/uploads", StaticFiles(directory="uploads/"), name="uploads")

origins = [
    "http://localhost:5173",
    "https://marketing.nsumt.uz",
    "https://face.nsumt.uz"
]   

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,         
    allow_credentials=True,
    allow_methods=["*"],           
    allow_headers=["*"],           
)


app.include_router(api_router)



if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host=settings.server.host, 
        port=settings.server.port, 
        reload=True
        )
