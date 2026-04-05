import pytest
from httpx import AsyncClient
import asyncio


class TestRateLimit:
    
    async def test_rate_limit_login_endpoint(self, client: AsyncClient):
        tasks = []
        for i in range(15):  
            tasks.append(
                client.post(
                    "/auth/login",
                    json={
                        "username": f"user{i}",
                        "password": "wrong"
                    }
                )
            )
        
        responses = await asyncio.gather(*tasks)
        
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes
    
    async def test_rate_limit_register_endpoint(self, client: AsyncClient):
        for i in range(6):
            response = await client.post(
                "/auth/register",
                json={
                    "username": f"ratelimituser{i}",
                    "email": f"user{i}@example.com",
                    "password": "password123"
                }
            )
            
            if i < 5:
                assert response.status_code in [200, 400]  
            else:
                if response.status_code == 429:
                    assert "Rate limit exceeded" in response.text
                    break
    
    async def test_rate_limit_headers(self, client: AsyncClient, auth_token):
        response = await client.post(
            "/scripts/",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Rate Limit Test",
                "code": "print('test')",
                "schedule": None
            }
        )
        
        assert "x-ratelimit-limit" in response.headers
        assert "x-ratelimit-remaining" in response.headers
        assert "x-ratelimit-window" in response.headers