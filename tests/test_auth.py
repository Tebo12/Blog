import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post(
        "/register",
        data={"email": "test@example.com", "login": "testuser", "password": "password123"},
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


@pytest.mark.asyncio
async def test_login_user(client: AsyncClient):
    await client.post(
        "/register",
        data={"email": "login@example.com", "login": "loginuser", "password": "password123"},
    )

    response = await client.post(
        "/login",
        data={"login": "loginuser", "password": "password123"},
    )
    assert response.status_code == 303
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_create_post_unauthorized(client: AsyncClient):
    response = await client.post(
        "/html/posts/new",
        data={"title": "Fail", "content": "Should not work", "authorId": 1},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "/login" in response.headers["location"]
