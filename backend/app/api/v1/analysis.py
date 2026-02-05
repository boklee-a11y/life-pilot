import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.models.data_source import DataSource
from app.api.deps import get_current_user
from app.services.analysis import process_all_sources

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/run")
async def run_analysis(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """모든 pending 소스에 대해 스크래핑 + AI 파싱을 실행합니다."""
    result = await db.execute(
        select(func.count()).where(
            DataSource.user_id == user.id,
        )
    )
    total = result.scalar()

    if total == 0:
        raise HTTPException(status_code=400, detail="No sources registered")

    # Trigger processing in background
    asyncio.create_task(process_all_sources(user.id))

    return {
        "status": "processing",
        "message": "Analysis started",
        "total_sources": total,
    }


@router.get("/status")
async def analysis_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """현재 분석 진행 상태를 조회합니다."""
    result = await db.execute(
        select(
            DataSource.status,
            func.count().label("count"),
        )
        .where(DataSource.user_id == user.id)
        .group_by(DataSource.status)
    )
    status_counts = {row.status: row.count for row in result}

    total = sum(status_counts.values())
    completed = status_counts.get("completed", 0)
    failed = status_counts.get("failed", 0)

    if total == 0:
        progress = 0
    else:
        progress = int((completed + failed) / total * 100)

    is_done = progress == 100

    return {
        "progress": progress,
        "is_done": is_done,
        "total": total,
        "status_breakdown": status_counts,
    }
