"""Basic API tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert "Banking RAG Agent" in response.json()["service"]


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@pytest.mark.asyncio
async def test_register_validation(client):
    response = await client.post("/auth/register", json={
        "name": "Test",
        "email": "invalid-email",
        "password": "123",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_unauthorized(client):
    response = await client.post("/auth/login", json={
        "email": "nonexistent@test.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_requires_auth(client):
    response = await client.post("/chat", json={"message": "Hello"})
    assert response.status_code == 401
