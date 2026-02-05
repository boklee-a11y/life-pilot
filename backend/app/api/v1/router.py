from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.onboarding import router as onboarding_router
from app.api.v1.sources import router as sources_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.scores import router as scores_router
from app.api.v1.actions import router as actions_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(onboarding_router)
api_router.include_router(sources_router)
api_router.include_router(analysis_router)
api_router.include_router(scores_router)
api_router.include_router(actions_router)
