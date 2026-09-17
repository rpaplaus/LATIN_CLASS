from fastapi import APIRouter

from app.api.v1.endpoints import (
    arena,
    auth,
    badges,
    chat,
    flashcards,
    health,
    lessons,
    media,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(
    lessons.router, prefix="/lessons", tags=["Lessons & AI Tutor"]
)
api_router.include_router(media.router, prefix="/media", tags=["Media & TTS"])
api_router.include_router(
    flashcards.router, prefix="/flashcards", tags=["Flashcards & Illustrator"]
)
api_router.include_router(
    badges.router, prefix="/badges", tags=["Roman Senate & Gamification"]
)
api_router.include_router(
    chat.router, prefix="/chat", tags=["Interactive Magister Chat & Web Search"]
)
api_router.include_router(
    arena.router, prefix="/arena", tags=["Arena Latium & Adaptive Flashcards"]
)

