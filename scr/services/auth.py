# services/auth.py (без HTTPException)
from typing import Tuple, Optional
import bcrypt
import jwt
from datetime import datetime, timedelta
from scr.core.config import Settings
from scr.models.user_model import UserModel
from scr.repositories.user_repository import UserRepository
from scr.services.email import EmailService

class AuthService:
    def __init__(self, repository: UserRepository, email_service: EmailService, config: Settings):
        self.repository = repository
        self.email_service = email_service
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
    
    async def login(self, username: str, password: str) -> Tuple[bool, Optional[str], Optional[str]]:
        user = await self.repository.get_user_by_username(username)
        
        if not user:
            return False, None, "Invalid credentials"
        
        if not user.get("is_verified"):
            return False, None, "Please verify your email"
        
        password_bytes = password.encode('utf-8')
        hash_bytes = user["password_hash"].encode('utf-8')
        
        if not bcrypt.checkpw(password_bytes, hash_bytes):
            return False, None, "Invalid credentials"
        
        token = self._create_access_token({"sub": user["username"]})
        return True, token, None
    
    def _create_access_token(self, data: dict) -> str:
        expire = datetime.utcnow() + timedelta(minutes=self.config.ACCESS_TOKEN_EXPIRE_MINUTES)
        data.update({"exp": expire})
        return jwt.encode(data, self.config.JWT_SECRET_KEY, algorithm=self.config.JWT_ALGORITHM)