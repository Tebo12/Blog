import pytest
from httpx import AsyncClient


async def get_auth_cookie(client: AsyncClient, login: str, password: str):
    await client.post(
        "/register",
        data={"email": f"{login}@example.com", "login": login, "password": password},
    )
    response = await client.post(
        "/login",
        data={"login": login, "password": password},
    )
    return response.cookies["access_token"]


@pytest.mark.asyncio
async def test_create_and_list_posts(client: AsyncClient):
    token = await get_auth_cookie(client, "postuser", "secret")
    cookies = {"access_token": token}

    response = await client.post(
        "/html/posts/new",
        data={"title": "My First Post", "content": "Content here"},
        cookies=cookies,
        follow_redirects=False,
    )

    assert response.status_code == 303

    response = await client.get("/")
    assert response.status_code == 200
    assert "My First Post" in response.text


@pytest.mark.asyncio
async def test_search_posts(client: AsyncClient):
    token = await get_auth_cookie(client, "searchuser", "secret")
    cookies = {"access_token": token}

    await client.post(
        "/html/posts/new",
        data={"title": "Python is great", "content": "..."},
        cookies=cookies,
        follow_redirects=False,
    )
    await client.post(
        "/html/posts/new",
        data={"title": "Java is okay", "content": "..."},
        cookies=cookies,
        follow_redirects=False,
    )

    response = await client.get("/?q=Python")
    assert response.status_code == 200
    assert "Python is great" in response.text
    assert "Java is okay" not in response.text


@pytest.mark.asyncio
async def test_favorites(client: AsyncClient):
    token = await get_auth_cookie(client, "favuser", "secret")
    cookies = {"access_token": token}

    resp = await client.post(
        "/html/posts/new",
        data={"title": "Fav Me", "content": "..."},
        cookies=cookies,
        follow_redirects=False,
    )
    assert resp.status_code == 303

    location = resp.headers["location"]
    post_id = location.split("/")[-1]

    resp = await client.post(f"/favorites/{post_id}/add", cookies=cookies, follow_redirects=False)
    assert resp.status_code == 303

    resp = await client.get("/profile", cookies=cookies)
    assert "Fav Me" in resp.text

    resp = await client.post(f"/favorites/{post_id}/remove", cookies=cookies, follow_redirects=False)
    assert resp.status_code == 303

    resp = await client.get("/profile", cookies=cookies)
