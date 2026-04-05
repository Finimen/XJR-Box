import pytest
from httpx import AsyncClient


class TestScriptsAPI:
    
    @pytest.fixture
    async def auth_token(self, client: AsyncClient):
        await client.post(
            "/auth/register",
            json={
                "username": "scriptuser",
                "email": "script@example.com",
                "password": "password123"
            }
        )
        
        response = await client.post(
            "/auth/login",
            json={
                "username": "scriptuser",
                "password": "password123"
            }
        )
        
        return response.json()["access_token"]
    
    async def test_create_script_success(self, client: AsyncClient, auth_token):
        response = await client.post(
            "/scripts/",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Test Script",
                "description": "This is a test script",
                "code": "print('Hello World')\nfor i in range(5):\n    print(i)",
                "schedule": "*/5 * * * *"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Script"
        assert data["description"] == "This is a test script"
        assert data["code"] == "print('Hello World')\nfor i in range(5):\n    print(i)"
        assert data["is_active"] is True
        assert "id" in data
    
    async def test_list_scripts(self, client: AsyncClient, auth_token):
        for i in range(3):
            await client.post(
                "/scripts/",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={
                    "name": f"Script {i}",
                    "code": f"print('Script {i}')",
                    "schedule": None
                }
            )
        
        response = await client.get(
            "/scripts/",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        assert all("name" in script for script in data)
    
    async def test_get_script_by_id(self, client: AsyncClient, auth_token):
        create_response = await client.post(
            "/scripts/",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Get Me Script",
                "code": "print('Get me!')",
                "schedule": "*/10 * * * *"
            }
        )
        script_id = create_response.json()["id"]
        
        response = await client.get(
            f"/scripts/{script_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == script_id
        assert data["name"] == "Get Me Script"
    
    async def test_update_script(self, client: AsyncClient, auth_token):
        create_response = await client.post(
            "/scripts/",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Original Name",
                "code": "print('Original')",
                "schedule": None
            }
        )
        script_id = create_response.json()["id"]
        
        response = await client.put(
            f"/scripts/{script_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Updated Name",
                "description": "Updated description"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"
    
    async def test_delete_script(self, client: AsyncClient, auth_token):
        create_response = await client.post(
            "/scripts/",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "To Delete",
                "code": "print('Delete me')",
                "schedule": None
            }
        )
        script_id = create_response.json()["id"]
        
        response = await client.delete(
            f"/scripts/{script_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 204
        
        get_response = await client.get(
            f"/scripts/{script_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert get_response.status_code == 404
    
    async def test_run_script_now(self, client: AsyncClient, auth_token):
        create_response = await client.post(
            "/scripts/",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Run Now Script",
                "code": "print('Running now!')",
                "schedule": None
            }
        )
        script_id = create_response.json()["id"]
        
        response = await client.post(
            f"/scripts/{script_id}/run",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "execution_id" in data
        assert data["message"] == "Script started"