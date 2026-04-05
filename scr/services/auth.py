from typing import Tuple, Optional
import bcrypt
import jwt
from datetime import datetime, timedelta
from scr.core.config import Settings
from scr.models.user_model import UserModel
from scr.repositories.user_repository import UserRepository
from scr.services.email import EmailService
from scr.services.redis import RedisService

class AuthService:
    def __init__(self, repository: UserRepository, email_service: EmailService, redis_service: RedisService, config: Settings):
        self.repository = repository
        self.email_service = email_service
        self.redis_service = redis_service  # 👈 Добавить!
        self.config = config
    
    async def register(self, username: str, email: str, password: str) -> Tuple[bool, Optional[dict], Optional[str]]:
        existing_user = await self.repository.get_user_by_username(username)
        if existing_user:
            return False, None, "Username already exists"
        
        existing_email = await self.repository.get_user_by_email(email)
        if existing_email:
            return False, None, "Email already registered"
        
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        user = await self.repository.create_user(UserModel(
            username = username,
            email = email,
            password_hash = password_hash.decode('utf-8'),
            ))
        
        try:
            await self.email_service.send_verification()
        except Exception as e:
            print(f"Email failed: {e}")
        
        return True, user, None
    
    async def login(self, username: str, password: str) -> Tuple[bool, str, Optional[str]]:
        user = await self.repository.get_user_by_username(username)
        
        if not user:
            return False, "", "Invalid credentials"
        
        password_bytes = password.encode('utf-8')
        hash_bytes = user.password_hash.encode('utf-8')
        
        if not bcrypt.checkpw(password_bytes, hash_bytes):
            return False, "", "Invalid credentials"
        
        token = self._create_access_token({"sub": user.username, "user_id" : user.id})

        if self.redis_service:
            expire_seconds = self.config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            await self.redis_service.store_user_token(user.id, token, expire_seconds)

        return True, token, None
    
    async def get_current_user(self, token: str) -> Tuple[bool, Optional[UserModel], Optional[str]]:
        try:
            payload = jwt.decode(
                token, 
                self.config.JWT_SECRET_KEY, 
                algorithms=[self.config.JWT_ALGORITHM]
            )
            
            if await self.redis_service.is_blacklisted(token):
                return False, None, "Token has been revoked"
            
            username = payload.get("sub")
            user_id = payload.get("user_id")
            
            if not username or not user_id:
                return False, None, "Invalid token payload"
            
            is_valid = await self.redis_service.is_token_valid(user_id, token)
            if not is_valid:
                return False, None, "Session expired, please login again"
            
            user = await self.repository.get_user_by_username(username)
            if not user:
                return False, None, "User not found"
            
            return True, user, None
            
        except jwt.ExpiredSignatureError:
            return False, None, "Token expired"
        except jwt.InvalidTokenError as e:
            return False, None, f"Invalid token: {str(e)}"
        except Exception as e:
            return False, None, f"Authentication error: {str(e)}"
    
    def _create_access_token(self, data: dict) -> str:
        expire = datetime.utcnow() + timedelta(minutes=self.config.ACCESS_TOKEN_EXPIRE_MINUTES)
        data.update({"exp": expire})
        return jwt.encode(data, self.config.JWT_SECRET_KEY, algorithm=self.config.JWT_ALGORITHM)