import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.middleware import SecurityHeadersMiddleware
from app.core.redis import close_redis_pool, get_redis_pool

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifespan: setup and teardown resources."""
    # Initialize connection pool eagerly
    get_redis_pool()
    yield
    # Teardown
    await close_redis_pool()
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Latium AI: Intelligent Latin Tutoring Platform Backend API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware for Web and Mobile Safari
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Defensive security HTTP headers
app.add_middleware(SecurityHeadersMiddleware)


# Global exception handler masking stack traces and logging internally (SEC-06)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Mask internal tracebacks and return sanitized error with correlation ID."""
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None) or {},
        )
    error_id = uuid.uuid4().hex[:8]
    logger.error(
        "Unhandled server error [error_id=%s] on %s %s: %s",
        error_id,
        request.method,
        request.url.path,
        exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Ocorreu um erro interno no servidor.",
            "error_id": error_id,
        },
    )


# Include API v1 router
app.include_router(api_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Redirect root path to interactive API docs."""
    return RedirectResponse(url="/docs")
