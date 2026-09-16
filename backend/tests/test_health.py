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


@pytest.mark.asyncio
async def test_global_exception_handler_sanitizes_errors() -> None:
    """Verify global exception handler catches unhandled exceptions and returns sanitized JSON with error_id (SEC-06)."""
    from fastapi import APIRouter
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    test_router = APIRouter()

    @test_router.get("/test-unhandled-error")
    async def _crash_endpoint() -> None:
        raise RuntimeError("Sensitive internal database secret stack trace")

    app.include_router(test_router)

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as test_client:
        response = await test_client.get("/test-unhandled-error")
        assert response.status_code == 500
        data = response.json()
        assert "error_id" in data
        assert "Sensitive" not in data["detail"]
        assert data["detail"] == "Ocorreu um erro interno no servidor."
