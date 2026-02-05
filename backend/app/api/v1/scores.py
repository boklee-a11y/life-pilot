"""
스코어 관련 API 엔드포인트
- 최신 스코어 조회
- 스코어 히스토리
- 동일 직군 대비 포지셔닝
- 수동 스코어링 재실행
"""

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.models.career_score import CareerScore
from app.models.score_history import ScoreHistory
from app.models.data_source import DataSource
from app.api.deps import get_current_user
from app.services.analysis import run_scoring

router = APIRouter(prefix="/scores", tags=["scores"])


@router.get("/latest")
async def get_latest_score(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """최신 커리어 스코어를 조회합니다."""
    result = await db.execute(
        select(CareerScore)
        .where(CareerScore.user_id == user.id)
        .order_by(desc(CareerScore.scored_at))
        .limit(1)
    )
    score = result.scalar_one_or_none()

    if not score:
        return {"has_score": False, "message": "아직 분석 결과가 없습니다."}

    return {
        "has_score": True,
        "id": str(score.id),
        "scores": {
            "expertise": float(score.expertise_score or 0),
            "influence": float(score.influence_score or 0),
            "consistency": float(score.consistency_score or 0),
            "marketability": float(score.marketability_score or 0),
            "potential": float(score.potential_score or 0),
            "total": float(score.total_score or 0),
        },
        "salary": {
            "min": score.estimated_salary_min,
            "max": score.estimated_salary_max,
        },
        "analysis_accuracy": float(score.analysis_accuracy or 0),
        "insights": score.ai_insights or {},
        "scored_at": score.scored_at.isoformat() if score.scored_at else None,
    }


@router.get("/history")
async def get_score_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """스코어 변화 히스토리를 조회합니다."""
    result = await db.execute(
        select(ScoreHistory)
        .where(ScoreHistory.user_id == user.id)
        .order_by(desc(ScoreHistory.created_at))
        .limit(20)
    )
    histories = result.scalars().all()

    return {
        "count": len(histories),
        "history": [
            {
                "id": str(h.id),
                "snapshot": h.snapshot,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in histories
        ],
    }


@router.get("/detail/{score_id}")
async def get_score_detail(
    score_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """특정 스코어의 상세 분석 결과를 조회합니다."""
    result = await db.execute(
        select(CareerScore).where(
            CareerScore.id == score_id,
            CareerScore.user_id == user.id,
        )
    )
    score = result.scalar_one_or_none()

    if not score:
        raise HTTPException(status_code=404, detail="Score not found")

    return {
        "id": str(score.id),
        "scores": {
            "expertise": float(score.expertise_score or 0),
            "influence": float(score.influence_score or 0),
            "consistency": float(score.consistency_score or 0),
            "marketability": float(score.marketability_score or 0),
            "potential": float(score.potential_score or 0),
            "total": float(score.total_score or 0),
        },
        "salary": {
            "min": score.estimated_salary_min,
            "max": score.estimated_salary_max,
        },
        "analysis_accuracy": float(score.analysis_accuracy or 0),
        "insights": score.ai_insights or {},
        "scored_at": score.scored_at.isoformat() if score.scored_at else None,
    }


@router.get("/market-position")
async def get_market_position(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """동일 직군 대비 포지셔닝 정보를 조회합니다."""
    # 최신 스코어 가져오기
    result = await db.execute(
        select(CareerScore)
        .where(CareerScore.user_id == user.id)
        .order_by(desc(CareerScore.scored_at))
        .limit(1)
    )
    my_score = result.scalar_one_or_none()

    if not my_score:
        raise HTTPException(status_code=404, detail="No score data available")

    # AI 인사이트에서 percentile 가져오기
    insights = my_score.ai_insights or {}
    percentile = insights.get("market_position_percentile", 50)

    # 같은 직군 사용자들의 평균 점수 (간단한 구현)
    same_category_result = await db.execute(
        select(
            func.avg(CareerScore.total_score),
            func.count(CareerScore.id),
        )
        .join(User, User.id == CareerScore.user_id)
        .where(User.job_category == user.job_category)
    )
    row = same_category_result.one()
    avg_total = float(row[0]) if row[0] else 50.0
    user_count = row[1] or 0

    return {
        "my_total_score": float(my_score.total_score or 0),
        "job_category": user.job_category,
        "years_of_experience": user.years_of_experience,
        "percentile": percentile,
        "category_avg_score": round(avg_total, 1),
        "category_user_count": user_count,
        "insights": {
            "strengths": insights.get("strengths", []),
            "weaknesses": insights.get("weaknesses", []),
            "overall_summary": insights.get("overall_summary", ""),
        },
    }


@router.post("/recalculate")
async def recalculate_scores(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """스코어링을 수동으로 재실행합니다."""
    # completed 소스가 있는지 확인
    result = await db.execute(
        select(func.count()).where(
            DataSource.user_id == user.id,
            DataSource.status == "completed",
        )
    )
    completed_count = result.scalar()

    if not completed_count:
        raise HTTPException(
            status_code=400,
            detail="No completed source data available for scoring",
        )

    # 백그라운드에서 스코어링 실행
    asyncio.create_task(run_scoring(user.id))

    return {
        "status": "processing",
        "message": "Scoring recalculation started",
    }
