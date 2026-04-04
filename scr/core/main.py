
from contextlib import asynccontextmanager
import logging
import os

from httpx import request

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting up")
    await init_db()

    yield

    logger.info("shutting down gracefully")
    await engine.dispose()
    logger.info("connection closed")

app = FastAPI(title="jxr-box", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router)
app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.exception_handler(404)
async def not_found_handler(reqest: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"messege" : "Endpoint not found"}
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT"))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)