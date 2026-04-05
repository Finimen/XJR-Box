from contextlib import asynccontextmanager
import logging
import os

from scr.core.config import settings

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from scr.databases.init_db import init_db
from scr.api.v1.auth import router as auth_router
from scr.api.v1.scripts import router as script_router
from scr.services.redis import RedisService
from scr.services.rate_limit import RateLimitMiddleware

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

    redis_service = RedisService()
    await redis_service.connect()
    app.state.redis_service = redis_service
    logger.info("✅ Redis connected")

    try:
        app.add_middleware(RateLimitMiddleware, redis_service=redis_service)
        logger.info("✅ Rate limit middleware added")
    except RuntimeError as e:
        logger.warning(f"Could not add rate limit middleware: {e}")

    from scr.services.scheduler import ScriptScheduler
    from scr.databases.session import async_session

    scheduler = ScriptScheduler(async_session, redis_service)
    await scheduler.start()
    app.state.scheduler = scheduler
    logger.info("✅ Scheduler started")

    yield

    if hasattr(app.state, 'scheduler'):
        await app.state.scheduler.shutdown()
        logger.info("✅ Scheduler stopped")
    
    if hasattr(app.state, 'redis_service'):
        await app.state.redis_service.disconnect()
        logger.info("✅ Redis disconnected")
    
    from scr.databases.session import engine
    await engine.dispose()
    logger.info("connection closed")


app = FastAPI(title="jxr-box", lifespan=lifespan)

app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router)
app.include_router(script_router)


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"message": "Endpoint not found"} 
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)