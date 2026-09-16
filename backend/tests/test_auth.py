import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient) -> None:
    """Test registering a new student account returns 201 and created profile."""
    payload = {
        "email": "cicero@roma.it",
        "password": "DeRePublica123!",
        "full_name": "Marcus Tullius Cicero",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["full_name"] == payload["full_name"]
    assert data["is_active"] is True
    assert data["is_superuser"] is False
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user: User) -> None:
    """Test registering with an existing email returns 400 Bad Request."""
    payload = {
        "email": test_user.email,
        "password": "AnotherPassword123!",
        "full_name": "Impostor",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_oauth2_success(client: AsyncClient, test_user: User) -> None:
    """Test logging in returns valid access_token, refresh_token and expires_in."""
    login_data = {
        "username": test_user.email,
        "password": "SecretPassword123!",
    }
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


@pytest.mark.asyncio
async def test_login_incorrect_password(client: AsyncClient, test_user: User) -> None:
    """Test logging in with invalid password returns 401 Unauthorized."""
    login_data = {
        "username": test_user.email,
        "password": "WrongPassword!",
    }
    response = await client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401
    assert "incorrect email or password" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_refresh_token_rotation_success(
    client: AsyncClient, test_user: User
) -> None:
    """Test that refreshing a token rotates the refresh token and invalidates the previous one."""
    # 1. Login to get initial tokens
    login_data = {
        "username": test_user.email,
        "password": "SecretPassword123!",
    }
    login_resp = await client.post("/api/v1/auth/login", data=login_data)
    assert login_resp.status_code == 200
    initial_tokens = login_resp.json()
    old_refresh_token = initial_tokens["refresh_token"]

    # 2. Call /refresh with valid refresh token
    refresh_resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": old_refresh_token}
    )
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["refresh_token"] != old_refresh_token

    # 3. Verify Refresh Token Rotation (RTR): Attempting to reuse old_refresh_token must fail
    reused_resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": old_refresh_token}
    )
    assert reused_resp.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(
    client: AsyncClient, test_user: User
) -> None:
    """Test that logout invalidates the refresh token in Redis."""
    # 1. Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "SecretPassword123!"},
    )
    assert login_resp.status_code == 200
    refresh_token = login_resp.json()["refresh_token"]

    # 2. Logout
    logout_resp = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": refresh_token}
    )
    assert logout_resp.status_code == 200

    # 3. Refresh with the logged-out token must now fail
    refresh_resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_resp.status_code == 401


@pytest.mark.asyncio
async def test_read_me_unauthorized(client: AsyncClient) -> None:
    """Test accessing /api/v1/auth/me without token returns 401 Unauthorized."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_read_me_authorized(client: AsyncClient, test_user: User) -> None:
    """Test accessing /api/v1/auth/me with valid Bearer token returns current user profile."""
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "SecretPassword123!"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name
