from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.schemas.onboarding import ProfileUpdateRequest
from app.schemas.auth import UserResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/profile", response_model=UserResponse)
async def update_profile(
    req: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user.job_category = req.job_category
    user.years_of_experience = req.years_of_experience
    if req.name:
        user.name = req.name

    await db.commit()
    await db.refresh(user)
    return user
