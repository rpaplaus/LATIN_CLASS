import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.models.user import User


@pytest.mark.asyncio
async def test_list_users_as_student_forbidden(
    client: AsyncClient, test_user: User
) -> None:
    """A regular student user must receive 403 Forbidden when trying to list all users."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/users/", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_users_as_superuser_success(
    client: AsyncClient, test_superuser: User
) -> None:
    """A superuser must be able to list users."""
    token = create_access_token(subject=str(test_superuser.id))
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/users/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(u["email"] == test_superuser.email for u in data)


@pytest.mark.asyncio
async def test_update_current_user_profile(
    client: AsyncClient, test_user: User
) -> None:
    """Authenticated user should be able to update their name and password."""
    token = create_access_token(subject=str(test_user.id))
    headers = {"Authorization": f"Bearer {token}"}
    update_payload = {
        "full_name": "Marcus Tullius Cicero Philosophus",
        "password": "NewCiceroPassword456!",
    }
    response = await client.patch(
        "/api/v1/users/me", json=update_payload, headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == update_payload["full_name"]

    # Verify that the new password works for login
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "NewCiceroPassword456!"},
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()
