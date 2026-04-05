from functools import wraps
from typing import Callable, Optional
from fastapi import Request, HTTPException
from scr.services.redis import RedisService


def rate_limit(max_requests: int, window_seconds: int, key_prefix: Optional[str] = None):
    """Декоратор для rate limiting на конкретных эндпоинтах"""
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            redis_service: RedisService = request.app.state.redis_service
            
            client_ip = request.client.host if request.client else "unknown"
            user_id = None
            
            if hasattr(request, "state") and hasattr(request.state, "user"):
                user_id = request.state.user.id
                key = f"rate_limit:user:{user_id}:{key_prefix or func.__name__}"
            else:
                key = f"rate_limit:ip:{client_ip}:{key_prefix or func.__name__}"
            
            allowed, remaining = await redis_service.check_rate_limit(
                key, max_requests, window_seconds
            )
            
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Max {max_requests} requests per {window_seconds} seconds."
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator