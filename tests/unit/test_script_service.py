import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from scr.services.script import ScriptService
from scr.models.script import Script
from scr.models.execution import Execution


@pytest.fixture
def script_service(mock_script_repo):
    return ScriptService(mock_script_repo)


@pytest.fixture
def mock_script_repo():
    repo = Mock()
    repo.create_script = AsyncMock()
    repo.get_script = AsyncMock()
    repo.get_user_scripts = AsyncMock()
    repo.update_script = AsyncMock()
    repo.delete_script = AsyncMock()
    repo.create_execution = AsyncMock()
    repo.update_execution = AsyncMock()
    repo.get_script_executions = AsyncMock()
    return repo

class TestScriptService:
    
    async def test_create_script_success(self, script_service, mock_script_repo):
        mock_script = Script(
            id=1,
            user_id=1,
            name="Test Script",
            code="print('Hello')",
            schedule="*/5 * * * *"
        )
        mock_script_repo.create_script.return_value = mock_script
        
        script = await script_service.create_script(
            user_id=1,
            name="Test Script",
            code="print('Hello')",
            description="Test description",
            schedule="*/5 * * * *"
        )
        
        assert script is not None
        assert script.name == "Test Script"
        mock_script_repo.create_script.assert_called_once()
    
    async def test_run_script_now(self, script_service, mock_script_repo):
        mock_script = Script(id=1, user_id=1, name="Test Script", code="print('test')")
        mock_script_repo.get_script.return_value = mock_script
        mock_script_repo.create_execution.return_value = Execution(id=1, script_id=1, status="running")
        
        with patch('asyncio.create_task'):
            execution_id = await script_service.run_script_now(
                script_id=1,
                user_id=1,
                background_tasks=Mock()
            )
        
        assert execution_id == 1
        mock_script_repo.create_execution.assert_called_once()
    
    async def test_get_user_scripts(self, script_service, mock_script_repo):
        scripts = [
            Script(id=1, name="Script 1"),
            Script(id=2, name="Script 2")
        ]
        mock_script_repo.get_user_scripts.return_value = scripts
        
        result = await script_service.get_user_scripts(user_id=1, skip=0, limit=10)
        
        assert len(result) == 2
        assert result[0].name == "Script 1"
    
    async def test_delete_script(self, script_service, mock_script_repo):
        mock_script_repo.delete_script.return_value = True
        
        deleted = await script_service.delete_script(script_id=1, user_id=1)
        
        assert deleted is True
        mock_script_repo.delete_script.assert_called_once_with(1, 1)