from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.redis import close_redis_pool, init_redis_pool


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifespan: setup and teardown resources."""
    # Startup
    init_redis_pool()
    yield
    # Shutdown
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

# Include API v1 router
app.include_router(api_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Redirect root path to interactive API docs."""
    return RedirectResponse(url="/docs")
