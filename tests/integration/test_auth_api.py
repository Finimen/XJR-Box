import pytest
from httpx import AsyncClient


class TestAuthAPI:
    
    async def test_register_user_success(self, client: AsyncClient):
        response = await client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "SecurePass123!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "created_at" in data
    
    async def test_register_duplicate_username(self, client: AsyncClient):
        await client.post(
            "/auth/register",
            json={
                "username": "duplicate",
                "email": "first@example.com",
                "password": "password123"
            }
        )
        
        response = await client.post(
            "/auth/register",
            json={
                "username": "duplicate",
                "email": "second@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 400
        assert "Username already exists" in response.text
    
    async def test_login_success(self, client: AsyncClient):
        await client.post(
            "/auth/register",
            json={
                "username": "loginuser",
                "email": "login@example.com",
                "password": "password123"
            }
        )
        
        response = await client.post(
            "/auth/login",
            json={
                "username": "loginuser",
                "password": "password123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_login_invalid_credentials(self, client: AsyncClient):
        response = await client.post(
            "/auth/login",
            json={
                "username": "nonexistent",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.text
    
    async def test_get_current_user_me(self, client: AsyncClient):
        await client.post(
            "/auth/register",
            json={
                "username": "meuser",
                "email": "me@example.com",
                "password": "password123"
            }
        )
        
        login_response = await client.post(
            "/auth/login",
            json={
                "username": "meuser",
                "password": "password123"
            }
        )
        token = login_response.json()["access_token"]
        
        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "meuser"
        assert data["email"] == "me@example.com"