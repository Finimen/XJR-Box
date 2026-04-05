import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock
from fastapi.testclient import TestClient

# Добавляем корневую директорию в PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from main import app
from scr.services.redis import RedisService
from scr.services.auth import AuthService
from scr.services.email import EmailService
from scr.repositories.user_repository import UserRepository
from scr.repositories.scripts_repository import ScriptRepository
from scr.core.config import settings


# ========== MOCK FIXTURES ==========

@pytest.fixture
def mock_redis_service():
    """Mock для Redis сервиса"""
    mock = Mock(spec=RedisService)
    mock.check_rate_limit = AsyncMock(return_value=(True, 99))
    mock.store_user_token = AsyncMock()
    mock.get_user_token = AsyncMock(return_value="mock_token")
    mock.is_token_valid = AsyncMock(return_value=True)
    mock.is_blacklisted = AsyncMock(return_value=False)
    mock.connect = AsyncMock()
    mock.disconnect = AsyncMock()
    mock.health_check = AsyncMock(return_value=True)
    mock.acquire_lock = AsyncMock(return_value=True)
    mock.release_lock = AsyncMock()
    mock.delete_user_token = AsyncMock()
    mock.delete_all_user_sessions = AsyncMock()
    return mock


@pytest.fixture
def mock_email_service():
    """Mock для Email сервиса"""
    mock = Mock(spec=EmailService)
    mock.send_verification = AsyncMock()
    return mock


@pytest.fixture
def mock_user_repo():
    """Mock для User Repository"""
    mock = Mock(spec=UserRepository)
    mock.get_user_by_username = AsyncMock()
    mock.get_user_by_email = AsyncMock()
    mock.create_user = AsyncMock()
    mock.update_user = AsyncMock()
    mock.delete_user = AsyncMock()
    mock.get_user_by_verification_token = AsyncMock()
    mock.update_user_verification = AsyncMock()
    mock.update_verification_token = AsyncMock()
    return mock


@pytest.fixture
def mock_script_repo():
    """Mock для Script Repository"""
    mock = Mock(spec=ScriptRepository)
    mock.create_script = AsyncMock()
    mock.get_script = AsyncMock()
    mock.get_user_scripts = AsyncMock()
    mock.update_script = AsyncMock()
    mock.delete_script = AsyncMock()
    mock.create_execution = AsyncMock()
    mock.update_execution = AsyncMock()
    mock.get_script_executions = AsyncMock()
    mock.get_all_user_executions = AsyncMock()
    mock.get_all_active_scripts = AsyncMock()
    mock.get_script_by_id = AsyncMock()
    mock.update_script_last_run = AsyncMock()
    return mock


@pytest.fixture
def auth_service(mock_user_repo, mock_email_service, mock_redis_service):
    """Фикстура для AuthService"""
    return AuthService(
        repository=mock_user_repo,
        email_service=mock_email_service,
        redis_service=mock_redis_service,
        config=settings
    )


@pytest.fixture
def script_service(mock_script_repo):
    """Фикстура для ScriptService"""
    from scr.services.script import ScriptService
    return ScriptService(mock_script_repo)


# ========== CLIENT FIXTURES (для интеграционных тестов) ==========

@pytest.fixture
def client():
    """Синхронный тестовый клиент для API тестов"""
    # Создаем моки
    mock_redis = Mock(spec=RedisService)
    mock_redis.check_rate_limit = AsyncMock(return_value=(True, 99))
    mock_redis.store_user_token = AsyncMock()
    mock_redis.get_user_token = AsyncMock(return_value="mock_token")
    mock_redis.is_token_valid = AsyncMock(return_value=True)
    mock_redis.is_blacklisted = AsyncMock(return_value=False)
    mock_redis.health_check = AsyncMock(return_value=True)
    
    mock_scheduler = Mock()
    mock_scheduler.start = AsyncMock()
    mock_scheduler.shutdown = AsyncMock()
    mock_scheduler.add_job = AsyncMock()
    mock_scheduler.remove_job = AsyncMock()
    mock_scheduler.update_job = AsyncMock()
    
    # Устанавливаем моки
    app.state.redis_service = mock_redis
    app.state.scheduler = mock_scheduler
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Очищаем
    if hasattr(app.state, 'redis_service'):
        del app.state.redis_service
    if hasattr(app.state, 'scheduler'):
        del app.state.scheduler


@pytest.fixture
def auth_token(client):
    """Фикстура для получения токена"""
    # Регистрация
    client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
    )
    
    # Логин
    response = client.post(
        "/auth/login",
        json={
            "username": "testuser",
            "password": "password123"
        }
    )
    
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.status_code}")
    
    return response.json()["access_token"]