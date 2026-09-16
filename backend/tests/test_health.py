import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient) -> None:
    """Verify health endpoint responds with 200 and healthy services."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["services"]["postgres"] == "healthy"
    assert data["services"]["redis"] == "healthy"
