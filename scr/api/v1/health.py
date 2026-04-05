from datetime import UTC, datetime
from typing import Dict, Any
import asyncio
import logging

from fastapi import APIRouter, Request, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from scr.core.di import get_redis_service, get_db
from scr.services.redis import RedisService

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


class HealthStatus:
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


async def check_database(db: AsyncSession) -> Dict[str, Any]:
    start_time = datetime.now(UTC)
    try:
        # Выполняем простой запрос для проверки
        await db.execute(text("SELECT 1"))
        latency = (datetime.now(UTC) - start_time).total_seconds() * 1000
        
        return {
            "status": HealthStatus.HEALTHY,
            "latency_ms": round(latency, 2),
            "message": "Database is reachable"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": HealthStatus.UNHEALTHY,
            "latency_ms": None,
            "message": f"Database connection failed: {str(e)}"
        }


async def check_redis(redis_service: RedisService) -> Dict[str, Any]:
    start_time = datetime.now(UTC)
    try:
        is_healthy = await redis_service.health_check()
        latency = (datetime.now(UTC) - start_time).total_seconds() * 1000
        
        if is_healthy:
            test_key = "health:test"
            await redis_service.cache_set(test_key, "ok", 5)
            value = await redis_service.cache_get(test_key)
            
            if value == "ok":
                return {
                    "status": HealthStatus.HEALTHY,
                    "latency_ms": round(latency, 2),
                    "message": "Redis is operational"
                }
        
        return {
            "status": HealthStatus.UNHEALTHY,
            "latency_ms": round(latency, 2),
            "message": "Redis ping failed"
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": HealthStatus.UNHEALTHY,
            "latency_ms": None,
            "message": f"Redis connection failed: {str(e)}"
        }


async def check_scheduler(request: Request) -> Dict[str, Any]:
    try:
        if not hasattr(request.app.state, 'scheduler'):
            return {
                "status": HealthStatus.DEGRADED,
                "message": "Scheduler not initialized"
            }
        
        scheduler = request.app.state.scheduler
        jobs = await scheduler.get_all_jobs()
        
        return {
            "status": HealthStatus.HEALTHY,
            "active_jobs": len(jobs),
            "message": f"Scheduler is running with {len(jobs)} active jobs"
        }
    except Exception as e:
        logger.error(f"Scheduler health check failed: {e}")
        return {
            "status": HealthStatus.UNHEALTHY,
            "message": f"Scheduler error: {str(e)}"
        }


@router.get("/health")
async def health_check(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    start_time = datetime.now(UTC)
    
    redis_service = await get_redis_service(request)
    
    db_check, redis_check, scheduler_check = await asyncio.gather(
        check_database(db),
        check_redis(redis_service),
        check_scheduler(request)
    )
    
    components = {
        "database": db_check,
        "redis": redis_check,
        "scheduler": scheduler_check
    }
    
    statuses = [comp["status"] for comp in components.values()]
    
    if HealthStatus.UNHEALTHY in statuses:
        overall_status = HealthStatus.UNHEALTHY
    elif HealthStatus.DEGRADED in statuses:
        overall_status = HealthStatus.DEGRADED
    else:
        overall_status = HealthStatus.HEALTHY
    
    response_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
    
    return {
        "status": overall_status,
        "timestamp": datetime.now(UTC).isoformat(),
        "response_time_ms": round(response_time, 2),
        "version": "1.0.0",
        "environment": "production", 
        "components": components
    }


@router.get("/health/live")
async def liveness_check() -> Dict[str, str]:
    return {
        "status": "alive",
        "timestamp": datetime.now(UTC).isoformat()
    }


@router.get("/health/ready")
async def readiness_check(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    redis_service = await get_redis_service(request)
    
    db_check, redis_check = await asyncio.gather(
        check_database(db),
        check_redis(redis_service)
    )
    
    is_ready = (
        db_check["status"] == HealthStatus.HEALTHY and
        redis_check["status"] == HealthStatus.HEALTHY
    )
    
    return {
        "ready": is_ready,
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": {
            "database": db_check["status"] == HealthStatus.HEALTHY,
            "redis": redis_check["status"] == HealthStatus.HEALTHY
        }
    }


@router.get("/health/metrics")
async def metrics(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    redis_service = await get_redis_service(request)
    
    # Детальные проверки
    db_check, redis_check, scheduler_check = await asyncio.gather(
        check_database(db),
        check_redis(redis_service),
        check_scheduler(request)
    )
    
    redis_stats = {}
    try:
        if hasattr(redis_service, 'redis') and redis_service.redis:
            info = await redis_service.redis.info()
            redis_stats = {
                "used_memory_mb": round(info.get("used_memory", 0) / 1024 / 1024, 2),
                "connected_clients": info.get("connected_clients", 0),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "hit_rate": info.get("keyspace_hit_rate", 0)
            }
    except Exception as e:
        logger.warning(f"Failed to get Redis stats: {e}")
    
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "uptime_seconds": _get_uptime(),
        "database": db_check,
        "redis": {
            **redis_check,
            "stats": redis_stats
        },
        "scheduler": scheduler_check,
        "system": {
            "python_version": "3.14",
            "platform": "windows"
        }
    }


def _get_uptime() -> float:
    try:
        import psutil
        import os
        process = psutil.Process(os.getpid())
        return time.time() - process.create_time()
    except ImportError:
        return 0.0
    except Exception:
        return 0.0