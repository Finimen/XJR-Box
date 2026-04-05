from datetime import datetime

from fastapi import APIRouter
from h11 import Request
from scr.core.di import get_redis_service

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check(request: Request):
    health_status = {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    redis_service = await get_redis_service(request)
    redis_healthy = await redis_service.health_check()
    health_status["redis"] = "healthy" if redis_healthy else "unhealthy"
    
    if not redis_healthy:
        health_status["status"] = "degraded"
    
    return health_status
