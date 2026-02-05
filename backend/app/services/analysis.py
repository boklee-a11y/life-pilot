"""
비동기 분석 파이프라인
URL 등록 → 스크래핑 → AI 파싱 → 스코어링 → DB 저장
"""

import uuid
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.data_source import DataSource
from app.models.user import User
from app.models.career_score import CareerScore
from app.models.score_history import ScoreHistory
from app.services.scraper import scrape_url
from app.services.ai_parser import parse_with_ai
from app.services.scoring import CareerScorer
from app.services.ai_scorer import get_ai_calibration, calculate_salary
from app.services.action_generator import generate_actions

logger = logging.getLogger(__name__)


async def process_source(source_id: UUID) -> None:
    """
    단일 데이터 소스를 스크래핑 + AI 파싱합니다.
    백그라운드 태스크로 실행됩니다.
    """
    async with async_session() as db:
        result = await db.execute(
            select(DataSource).where(DataSource.id == source_id)
        )
        source = result.scalar_one_or_none()
        if not source:
            logger.error(f"Source {source_id} not found")
            return

        # Step 1: Scraping
        source.status = "scraping"
        await db.commit()

        logger.info(f"Scraping {source.source_url} ({source.platform})")
        scrape_result = await scrape_url(source.source_url, source.platform)

        if not scrape_result["success"]:
            source.status = "failed"
            source.error_message = scrape_result.get("error", "Scraping failed")
            await db.commit()
            return

        source.scraped_html = scrape_result["raw_html"]

        # Step 2: AI Parsing
        source.status = "parsing"
        await db.commit()

        logger.info(f"Parsing {source.source_url} with Claude API")
        parsed_data = await parse_with_ai(
            scrape_result["cleaned_text"],
            source.platform,
            source.source_url,
        )

        # Step 3: Save results
        source.parsed_data = parsed_data
        source.status = "completed"
        source.last_scraped_at = datetime.now(timezone.utc)
        source.error_message = None
        await db.commit()

        logger.info(f"Source {source_id} processing completed")


async def process_all_sources(user_id: UUID) -> None:
    """유저의 모든 pending 소스를 처리한 뒤, 스코어링을 실행합니다."""
    async with async_session() as db:
        result = await db.execute(
            select(DataSource).where(
                DataSource.user_id == user_id,
                DataSource.status.in_(["pending"]),
            )
        )
        sources = result.scalars().all()

    # 스크래핑 + 파싱
    for source in sources:
        await process_source(source.id)

    # 스코어링 실행
    await run_scoring(user_id)


async def run_scoring(user_id: UUID) -> dict | None:
    """
    유저의 모든 completed 소스 데이터를 기반으로 5대 영역 스코어링을 실행합니다.

    1. parsed_data 수집
    2. 규칙 기반 정량 스코어 산출
    3. Claude API 정성 분석 보정
    4. 연봉 범위 산출
    5. CareerScore + ScoreHistory 저장
    """
    async with async_session() as db:
        # 유저 정보 조회
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            logger.error(f"User {user_id} not found for scoring")
            return None

        # completed 소스의 parsed_data 수집
        sources_result = await db.execute(
            select(DataSource).where(
                DataSource.user_id == user_id,
                DataSource.status == "completed",
                DataSource.parsed_data.isnot(None),
            )
        )
        sources = sources_result.scalars().all()

        if not sources:
            logger.warning(f"No completed sources for user {user_id}")
            return None

        sources_data = [s.parsed_data for s in sources if s.parsed_data]

        # Step 1: 규칙 기반 정량 스코어
        scorer = CareerScorer(
            sources_data=sources_data,
            job_category=user.job_category or "other",
            years_of_experience=user.years_of_experience or 0,
        )
        base_scores = scorer.calculate_all()
        logger.info(f"Base scores for user {user_id}: {base_scores}")

        # Step 2: Claude API 정성 분석 보정
        calibration = await get_ai_calibration(
            sources_data=sources_data,
            scores=base_scores,
            job_category=user.job_category or "other",
            years=user.years_of_experience or 0,
        )

        # Step 3: 보정 적용
        adjustments = calibration.get("adjustments", {})
        final_scores = {}
        for area in ["expertise", "influence", "consistency", "marketability", "potential"]:
            adj = adjustments.get(area, 0)
            final_scores[area] = round(
                max(0, min(100, base_scores[area] + adj)), 1
            )

        # 종합 점수 재계산
        weights = {
            "expertise": 0.25,
            "influence": 0.20,
            "consistency": 0.20,
            "marketability": 0.20,
            "potential": 0.15,
        }
        final_scores["total"] = round(
            sum(final_scores[k] * weights[k] for k in weights), 1
        )
        final_scores["analysis_accuracy"] = base_scores.get("analysis_accuracy", 30)

        # Step 4: 연봉 산출
        salary_adj = calibration.get("salary_adjustment_percent", 0)
        salary_min, salary_max = calculate_salary(
            base_scores=final_scores,
            job_category=user.job_category or "other",
            years=user.years_of_experience or 0,
            salary_adjustment_percent=salary_adj,
        )

        # Step 5: AI 인사이트 통합
        insights = calibration.get("insights", {})
        insights["base_scores"] = base_scores
        insights["adjustments"] = adjustments
        insights["market_position_percentile"] = calibration.get(
            "market_position_percentile", 50
        )

        # Step 6: CareerScore 저장
        now = datetime.now(timezone.utc)
        career_score = CareerScore(
            id=uuid.uuid4(),
            user_id=user_id,
            expertise_score=final_scores["expertise"],
            influence_score=final_scores["influence"],
            consistency_score=final_scores["consistency"],
            marketability_score=final_scores["marketability"],
            potential_score=final_scores["potential"],
            total_score=final_scores["total"],
            estimated_salary_min=salary_min,
            estimated_salary_max=salary_max,
            analysis_accuracy=final_scores["analysis_accuracy"],
            ai_insights=insights,
            scored_at=now,
            created_at=now,
        )
        db.add(career_score)

        # Step 7: ScoreHistory 저장
        snapshot = {
            **final_scores,
            "salary_min": salary_min,
            "salary_max": salary_max,
        }
        score_history = ScoreHistory(
            id=uuid.uuid4(),
            user_id=user_id,
            score_id=career_score.id,
            snapshot=snapshot,
            created_at=now,
        )
        db.add(score_history)

        await db.commit()

        logger.info(
            f"Scoring completed for user {user_id}: "
            f"total={final_scores['total']}, "
            f"salary={salary_min}~{salary_max}만원"
        )

    # Step 8: 액션 추천 생성 (별도 세션)
    try:
        await generate_actions(user_id, career_score.id)
    except Exception as e:
        logger.error(f"Action generation failed for user {user_id}: {e}")

    return {
        "scores": final_scores,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "insights": insights,
    }
