import time
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from scr.services.redis import RedisService


class RateLimitMiddleware(BaseHTTPMiddleware):
    
    def __init__(self, app, redis_service: RedisService):
        super().__init__(app)
        self.redis_service = redis_service
        self.default_limits = {
            "default": "100/minute",    
            "/auth/login": "10/minute",  
            "/auth/register": "5/hour",  
            "/scripts/": "50/minute",    
        }
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        
        limit_config = self._get_limit_for_path(path)
        
        if limit_config:
            key = f"rate_limit:{client_ip}:{path}"
            max_requests, window_seconds = self._parse_limit(limit_config)
            
            allowed, remaining = await self.redis_service.check_rate_limit(
                key, max_requests, window_seconds
            )
            
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Too many requests",
                        "message": f"Rate limit exceeded. Max {max_requests} requests per {window_seconds} seconds.",
                        "retry_after": window_seconds
                    },
                    headers={"Retry-After": str(window_seconds)}
                )
            
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(max_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Window"] = str(window_seconds)
            
            return response
        
        return await call_next(request)
    
    def _get_limit_for_path(self, path: str) -> str | None:
        if path in self.default_limits:
            return self.default_limits[path]
        
        for route_path, limit in self.default_limits.items():
            if route_path.endswith("/") and path.startswith(route_path):
                return limit
            elif path.startswith(route_path) and route_path != "/":
                return limit
        
        return self.default_limits.get("default")
    
    def _parse_limit(self, limit: str) -> Tuple[int, int]:
        parts = limit.split('/')
        if len(parts) != 2:
            return 100, 60 
        
        max_requests = int(parts[0])
        time_unit = parts[1]
        
        window_map = {
            "second": 1,
            "minute": 60,
            "hour": 3600,
            "day": 86400
        }
        
        window_seconds = window_map.get(time_unit, 60)
        return max_requests, window_seconds