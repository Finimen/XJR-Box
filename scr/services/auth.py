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
    
    async def get_current_user(self, token: str) -> Tuple[bool, Optional[UserModel], Optional[str]]:
        """
        Получение текущего пользователя из токена.
        Returns: (success, user, error_message)
        """
        try:
            # 1. Проверяем JWT
            payload = jwt.decode(
                token, 
                self.config.JWT_SECRET_KEY, 
                algorithms=[self.config.JWT_ALGORITHM]
            )
            
            # 2. Проверяем, не в черном ли списке токен
            if await self.redis_service.is_blacklisted(token):
                return False, None, "Token has been revoked"
            
            # 3. Достаем username из payload
            username = payload.get("sub")
            user_id = payload.get("user_id")
            
            if not username or not user_id:
                return False, None, "Invalid token payload"
            
            # 4. Проверяем, совпадает ли токен с сохраненным в Redis
            is_valid = await self.redis_service.is_token_valid(user_id, token)
            if not is_valid:
                return False, None, "Session expired, please login again"
            
            # 5. Получаем пользователя из БД
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