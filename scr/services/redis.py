import json
from typing import Optional, Any
from redis import asyncio as aioredis
from scr.core.config import settings

class RedisService:
    def __init__(self):
        self.redis = None
        self._is_connected = False
    
    async def connect(self) -> None:
        """Подключение к Redis"""
        if not self._is_connected:
            try:
                self.redis = await aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=20  # Пул соединений
                )
                await self.redis.ping()
                self._is_connected = True
                print(f"✅ Redis connected: {settings.REDIS_URL}")
            except Exception as e:
                print(f"❌ Redis connection failed: {e}")
                raise
    
    async def disconnect(self) -> None:
        if self.redis and self._is_connected:
            await self.redis.close()
            self._is_connected = False
            print("✅ Redis disconnected")
    
    async def _ensure_connection(self):
        if not self._is_connected or not self.redis:
            await self.connect()
    
    async def store_user_token(self, user_id: int, token: str, expire_seconds: int) -> None:
        await self._ensure_connection()
        key = f"user:{user_id}:token"
        await self.redis.setex(key, expire_seconds, token)
    
    async def get_user_token(self, user_id: int) -> Optional[str]:
        await self._ensure_connection()
        key = f"user:{user_id}:token"
        return await self.redis.get(key)
    
    async def delete_user_token(self, user_id: int) -> None:
        await self._ensure_connection()
        key = f"user:{user_id}:token"
        await self.redis.delete(key)
    
    async def is_token_valid(self, user_id: int, token: str) -> bool:
        await self._ensure_connection()
        stored_token = await self.get_user_token(user_id)
        return stored_token == token
    
    async def blacklist_token(self, token: str, expire_seconds: int) -> None:
        await self._ensure_connection()
        key = f"blacklist:{token}"
        await self.redis.setex(key, expire_seconds, "blacklisted")
    
    async def is_blacklisted(self, token: str) -> bool:
        await self._ensure_connection()
        key = f"blacklist:{token}"
        return await self.redis.exists(key) == 1
    
    async def create_session(self, session_id: str, user_id: int, expire_seconds: int = 86400) -> None:
        await self._ensure_connection()
        key = f"session:{session_id}"
        await self.redis.setex(key, expire_seconds, str(user_id))
    
    async def get_session_user(self, session_id: str) -> Optional[int]:
        await self._ensure_connection()
        key = f"session:{session_id}"
        user_id = await self.redis.get(key)
        return int(user_id) if user_id else None
    
    async def delete_session(self, session_id: str) -> None:
        await self._ensure_connection()
        key = f"session:{session_id}"
        await self.redis.delete(key)
    
    async def delete_all_user_sessions(self, user_id: int) -> None:
        await self._ensure_connection()
        pattern = f"session:*"
        cursor = 0
        deleted = 0
        
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            for key in keys:
                session_user_id = await self.redis.get(key)
                if session_user_id and int(session_user_id) == user_id:
                    await self.redis.delete(key)
                    deleted += 1
            if cursor == 0:
                break
        
        return deleted
    
    async def cache_get(self, key: str) -> Optional[Any]:
        await self._ensure_connection()
        data = await self.redis.get(key)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return data
        return None
    
    async def cache_set(self, key: str, value: Any, expire_seconds: int = 300) -> None:
        await self._ensure_connection()
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        await self.redis.setex(key, expire_seconds, value)
    
    async def cache_delete(self, key: str) -> None:
        await self._ensure_connection()
        await self.redis.delete(key)
    
    async def cache_delete_pattern(self, pattern: str) -> int:
        await self._ensure_connection()
        cursor = 0
        deleted = 0
        
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            if keys:
                await self.redis.delete(*keys)
                deleted += len(keys)
            if cursor == 0:
                break
        
        return deleted
    
    # ========== RATE LIMITING (ограничение запросов) ==========
    
    async def check_rate_limit(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
        await self._ensure_connection()
        
        current = await self.redis.get(key)
        
        if current is None:
            await self.redis.setex(key, window_seconds, 1)
            return True, max_requests - 1
        
        count = int(current)
        if count >= max_requests:
            ttl = await self.redis.ttl(key)
            return False, 0
        
        await self.redis.incr(key)
        return True, max_requests - (count + 1)
    
    async def health_check(self) -> bool:
        try:
            await self._ensure_connection()
            await self.redis.ping()
            return True
        except Exception:
            return False
    
    async def flush_all(self) -> None:
        await self._ensure_connection()
        await self.redis.flushall()