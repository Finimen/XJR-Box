import pytest
import bcrypt
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from scr.services.auth import AuthService
from scr.models.user_model import UserModel


class TestAuthService:
    
    @pytest.mark.asyncio
    async def test_register_success(self, auth_service, mock_user_repo):
        """Тест успешной регистрации"""
        mock_user_repo.get_user_by_username.return_value = None
        mock_user_repo.get_user_by_email.return_value = None
        
        mock_user = UserModel(
            id=1,
            username="testuser",
            email="test@example.com",
            password_hash="hash",
            created_at=datetime.utcnow()
        )
        mock_user_repo.create_user.return_value = mock_user
        
        success, user, error = await auth_service.register(
            username="testuser",
            email="test@example.com",
            password="password123"
        )
        
        assert success is True
        assert user is not None
        assert error is None
        mock_user_repo.create_user.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, auth_service, mock_user_repo):
        """Тест регистрации с существующим username"""
        existing_user = UserModel(username="testuser", email="old@example.com")
        mock_user_repo.get_user_by_username.return_value = existing_user
        
        success, user, error = await auth_service.register(
            username="testuser",
            email="new@example.com",
            password="password123"
        )
        
        assert success is False
        assert user is None
        assert error == "Username already exists"
        mock_user_repo.create_user.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, mock_user_repo, mock_redis_service):
        """Тест успешного логина"""
        password = "password123"
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        user = UserModel(
            id=1,
            username="testuser",
            email="test@example.com",
            password_hash=password_hash.decode()
        )
        mock_user_repo.get_user_by_username.return_value = user
        
        success, token, error = await auth_service.login(
            username="testuser",
            password=password
        )
        
        assert success is True
        assert token is not None
        assert error is None
        mock_redis_service.store_user_token.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_login_invalid_password(self, auth_service, mock_user_repo):
        """Тест логина с неверным паролем"""
        password = "correct_password"
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        user = UserModel(
            id=1,
            username="testuser",
            password_hash=password_hash.decode()
        )
        mock_user_repo.get_user_by_username.return_value = user
        
        success, token, error = await auth_service.login(
            username="testuser",
            password="wrong_password"
        )
        
        assert success is False
        assert token == ""
        assert error == "Invalid credentials"
    
    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, auth_service, mock_user_repo, mock_redis_service):
        """Тест получения текущего пользователя по валидному токену"""
        import jwt
        from datetime import datetime, timedelta
        
        # Создаем валидный токен
        token_data = {"sub": "testuser", "user_id": 1}
        token = jwt.encode(
            token_data,
            auth_service.config.JWT_SECRET_KEY,
            algorithm=auth_service.config.JWT_ALGORITHM
        )
        
        user = UserModel(id=1, username="testuser", email="test@example.com")
        mock_user_repo.get_user_by_username.return_value = user
        mock_redis_service.is_token_valid.return_value = True
        
        success, user_result, error = await auth_service.get_current_user(token)
        
        assert success is True
        assert user_result is not None
        assert user_result.username == "testuser"
    
    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self, auth_service):
        """Тест с просроченным токеном"""
        import jwt
        from datetime import datetime, timedelta
        
        # Создаем просроченный токен
        token_data = {
            "sub": "testuser", 
            "user_id": 1,
            "exp": datetime.utcnow() - timedelta(minutes=1)
        }
        token = jwt.encode(
            token_data,
            auth_service.config.JWT_SECRET_KEY,
            algorithm=auth_service.config.JWT_ALGORITHM
        )
        
        success, user, error = await auth_service.get_current_user(token)
        
        assert success is False
        assert user is None
        assert error == "Token expired"