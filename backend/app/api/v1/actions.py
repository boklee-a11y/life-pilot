"""
액션 추천 API 엔드포인트
- 액션 목록 (필터/정렬)
- 액션 완료 토글 (+ 재스캔 트리거)
- 액션 북마크 토글
"""

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.models.action_recommendation import ActionRecommendation
from app.api.deps import get_current_user
from app.services.analysis import run_scoring

router = APIRouter(prefix="/actions", tags=["actions"])


@router.get("")
async def get_actions(
    tag: str | None = Query(None, description="태그 필터"),
    area: str | None = Query(None, description="영역 필터 (expertise, influence, ...)"),
    sort: str = Query("impact", description="정렬: impact, difficulty, recent"),
    completed: bool | None = Query(None, description="완료 상태 필터"),
    bookmarked: bool | None = Query(None, description="북마크 필터"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """추천 액션 목록을 조회합니다."""
    query = select(ActionRecommendation).where(
        ActionRecommendation.user_id == user.id
    )

    # 필터
    if area:
        query = query.where(ActionRecommendation.target_area == area)
    if completed is not None:
        query = query.where(ActionRecommendation.is_completed == completed)
    if bookmarked is not None:
        query = query.where(ActionRecommendation.is_bookmarked == bookmarked)

    # 정렬
    if sort == "impact":
        query = query.order_by(desc(ActionRecommendation.impact_percent))
    elif sort == "difficulty":
        difficulty_order = {"easy": 1, "medium": 2, "hard": 3}
        query = query.order_by(asc(ActionRecommendation.difficulty))
    else:
        query = query.order_by(desc(ActionRecommendation.created_at))

    result = await db.execute(query)
    actions = result.scalars().all()

    # 태그 필터 (DB 배열 필터보다 Python에서 처리)
    if tag:
        actions = [a for a in actions if a.tags and tag in a.tags]

    return {
        "count": len(actions),
        "actions": [
            {
                "id": str(a.id),
                "title": a.title,
                "description": a.description,
                "impact_percent": float(a.impact_percent) if a.impact_percent else None,
                "target_area": a.target_area,
                "difficulty": a.difficulty,
                "estimated_duration": a.estimated_duration,
                "tags": a.tags or [],
                "cta_label": a.cta_label,
                "cta_url": a.cta_url,
                "is_completed": a.is_completed,
                "completed_at": a.completed_at.isoformat() if a.completed_at else None,
                "is_bookmarked": a.is_bookmarked,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in actions
        ],
    }


@router.patch("/{action_id}/complete")
async def toggle_complete(
    action_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """액션 완료 상태를 토글합니다. 완료 시 재스코어링을 트리거합니다."""
    result = await db.execute(
        select(ActionRecommendation).where(
            ActionRecommendation.id == action_id,
            ActionRecommendation.user_id == user.id,
        )
    )
    action = result.scalar_one_or_none()

    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    action.is_completed = not action.is_completed
    action.completed_at = datetime.now(timezone.utc) if action.is_completed else None
    await db.commit()

    # 완료 시 백그라운드에서 재스코어링
    if action.is_completed:
        asyncio.create_task(run_scoring(user.id))

    return {
        "id": str(action.id),
        "is_completed": action.is_completed,
        "completed_at": action.completed_at.isoformat() if action.completed_at else None,
        "message": "액션을 완료했습니다! 점수가 곧 업데이트됩니다." if action.is_completed else "액션 완료를 취소했습니다.",
    }


@router.patch("/{action_id}/bookmark")
async def toggle_bookmark(
    action_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """액션 북마크 상태를 토글합니다."""
    result = await db.execute(
        select(ActionRecommendation).where(
            ActionRecommendation.id == action_id,
            ActionRecommendation.user_id == user.id,
        )
    )
    action = result.scalar_one_or_none()

    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    action.is_bookmarked = not action.is_bookmarked
    await db.commit()

    return {
        "id": str(action.id),
        "is_bookmarked": action.is_bookmarked,
    }
