"""
시장 데이터 시드 스크립트
- 직군별/연차별 연봉 범위
- 주요 스킬별 수요 레벨
"""

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.market_data import MarketData

# 직군별/연차별 연봉 데이터 (만원 단위)
SALARY_DATA = [
    # 개발
    {"job_category": "dev", "years_range": "0-2", "avg_salary_min": 3200, "avg_salary_max": 4500},
    {"job_category": "dev", "years_range": "3-5", "avg_salary_min": 4500, "avg_salary_max": 6500},
    {"job_category": "dev", "years_range": "6-9", "avg_salary_min": 6000, "avg_salary_max": 9000},
    {"job_category": "dev", "years_range": "10-14", "avg_salary_min": 8000, "avg_salary_max": 12000},
    {"job_category": "dev", "years_range": "15+", "avg_salary_min": 10000, "avg_salary_max": 18000},
    # 디자인
    {"job_category": "design", "years_range": "0-2", "avg_salary_min": 2800, "avg_salary_max": 3800},
    {"job_category": "design", "years_range": "3-5", "avg_salary_min": 3800, "avg_salary_max": 5500},
    {"job_category": "design", "years_range": "6-9", "avg_salary_min": 5000, "avg_salary_max": 7500},
    {"job_category": "design", "years_range": "10-14", "avg_salary_min": 7000, "avg_salary_max": 10000},
    {"job_category": "design", "years_range": "15+", "avg_salary_min": 9000, "avg_salary_max": 15000},
    # PM
    {"job_category": "pm", "years_range": "0-2", "avg_salary_min": 3000, "avg_salary_max": 4200},
    {"job_category": "pm", "years_range": "3-5", "avg_salary_min": 4200, "avg_salary_max": 6000},
    {"job_category": "pm", "years_range": "6-9", "avg_salary_min": 5500, "avg_salary_max": 8500},
    {"job_category": "pm", "years_range": "10-14", "avg_salary_min": 8000, "avg_salary_max": 12000},
    {"job_category": "pm", "years_range": "15+", "avg_salary_min": 10000, "avg_salary_max": 17000},
    # 마케팅
    {"job_category": "marketing", "years_range": "0-2", "avg_salary_min": 2800, "avg_salary_max": 3800},
    {"job_category": "marketing", "years_range": "3-5", "avg_salary_min": 3800, "avg_salary_max": 5500},
    {"job_category": "marketing", "years_range": "6-9", "avg_salary_min": 5000, "avg_salary_max": 7500},
    {"job_category": "marketing", "years_range": "10-14", "avg_salary_min": 7000, "avg_salary_max": 10000},
    {"job_category": "marketing", "years_range": "15+", "avg_salary_min": 9000, "avg_salary_max": 14000},
    # 데이터
    {"job_category": "data", "years_range": "0-2", "avg_salary_min": 3500, "avg_salary_max": 4800},
    {"job_category": "data", "years_range": "3-5", "avg_salary_min": 5000, "avg_salary_max": 7000},
    {"job_category": "data", "years_range": "6-9", "avg_salary_min": 6500, "avg_salary_max": 9500},
    {"job_category": "data", "years_range": "10-14", "avg_salary_min": 8500, "avg_salary_max": 13000},
    {"job_category": "data", "years_range": "15+", "avg_salary_min": 11000, "avg_salary_max": 18000},
    # 기타
    {"job_category": "other", "years_range": "0-2", "avg_salary_min": 2800, "avg_salary_max": 3800},
    {"job_category": "other", "years_range": "3-5", "avg_salary_min": 3800, "avg_salary_max": 5500},
    {"job_category": "other", "years_range": "6-9", "avg_salary_min": 5000, "avg_salary_max": 7500},
    {"job_category": "other", "years_range": "10-14", "avg_salary_min": 7000, "avg_salary_max": 10000},
    {"job_category": "other", "years_range": "15+", "avg_salary_min": 8000, "avg_salary_max": 14000},
]

# 주요 스킬별 수요 레벨 (1-10)
SKILL_DEMAND = [
    # 개발 스킬
    {"job_category": "dev", "skill_name": "Python", "demand_level": 9},
    {"job_category": "dev", "skill_name": "JavaScript", "demand_level": 9},
    {"job_category": "dev", "skill_name": "TypeScript", "demand_level": 9},
    {"job_category": "dev", "skill_name": "React", "demand_level": 9},
    {"job_category": "dev", "skill_name": "Next.js", "demand_level": 8},
    {"job_category": "dev", "skill_name": "Node.js", "demand_level": 8},
    {"job_category": "dev", "skill_name": "Java", "demand_level": 8},
    {"job_category": "dev", "skill_name": "Spring", "demand_level": 8},
    {"job_category": "dev", "skill_name": "Kotlin", "demand_level": 7},
    {"job_category": "dev", "skill_name": "Go", "demand_level": 7},
    {"job_category": "dev", "skill_name": "Rust", "demand_level": 7},
    {"job_category": "dev", "skill_name": "AWS", "demand_level": 9},
    {"job_category": "dev", "skill_name": "Docker", "demand_level": 8},
    {"job_category": "dev", "skill_name": "Kubernetes", "demand_level": 8},
    {"job_category": "dev", "skill_name": "PostgreSQL", "demand_level": 7},
    {"job_category": "dev", "skill_name": "MongoDB", "demand_level": 6},
    {"job_category": "dev", "skill_name": "Redis", "demand_level": 7},
    {"job_category": "dev", "skill_name": "GraphQL", "demand_level": 6},
    {"job_category": "dev", "skill_name": "Flutter", "demand_level": 7},
    {"job_category": "dev", "skill_name": "Swift", "demand_level": 6},
    {"job_category": "dev", "skill_name": "AI/ML", "demand_level": 10},
    {"job_category": "dev", "skill_name": "LLM", "demand_level": 10},
    {"job_category": "dev", "skill_name": "DevOps", "demand_level": 8},
    {"job_category": "dev", "skill_name": "CI/CD", "demand_level": 7},
    # 디자인 스킬
    {"job_category": "design", "skill_name": "Figma", "demand_level": 10},
    {"job_category": "design", "skill_name": "UI/UX", "demand_level": 9},
    {"job_category": "design", "skill_name": "Product Design", "demand_level": 9},
    {"job_category": "design", "skill_name": "Design System", "demand_level": 8},
    {"job_category": "design", "skill_name": "Prototyping", "demand_level": 7},
    {"job_category": "design", "skill_name": "User Research", "demand_level": 8},
    {"job_category": "design", "skill_name": "Motion Design", "demand_level": 6},
    {"job_category": "design", "skill_name": "Adobe Suite", "demand_level": 6},
    # PM 스킬
    {"job_category": "pm", "skill_name": "Product Strategy", "demand_level": 9},
    {"job_category": "pm", "skill_name": "Data Analysis", "demand_level": 8},
    {"job_category": "pm", "skill_name": "A/B Testing", "demand_level": 7},
    {"job_category": "pm", "skill_name": "Agile/Scrum", "demand_level": 8},
    {"job_category": "pm", "skill_name": "SQL", "demand_level": 7},
    {"job_category": "pm", "skill_name": "Growth Hacking", "demand_level": 7},
    # 데이터 스킬
    {"job_category": "data", "skill_name": "Python", "demand_level": 10},
    {"job_category": "data", "skill_name": "SQL", "demand_level": 9},
    {"job_category": "data", "skill_name": "Machine Learning", "demand_level": 9},
    {"job_category": "data", "skill_name": "Deep Learning", "demand_level": 8},
    {"job_category": "data", "skill_name": "Spark", "demand_level": 7},
    {"job_category": "data", "skill_name": "Tableau", "demand_level": 6},
    {"job_category": "data", "skill_name": "Statistics", "demand_level": 8},
]


def _get_years_range(years: int) -> str:
    """연차를 연차 구간 문자열로 변환"""
    if years <= 2:
        return "0-2"
    elif years <= 5:
        return "3-5"
    elif years <= 9:
        return "6-9"
    elif years <= 14:
        return "10-14"
    else:
        return "15+"


async def seed_market_data(db: AsyncSession) -> int:
    """시장 데이터를 DB에 시드. 이미 데이터가 있으면 스킵."""
    result = await db.execute(select(func.count()).select_from(MarketData))
    existing = result.scalar()
    if existing and existing > 0:
        return 0

    count = 0
    now = datetime.now(timezone.utc)

    # 연봉 데이터
    for entry in SALARY_DATA:
        db.add(MarketData(
            id=uuid.uuid4(),
            job_category=entry["job_category"],
            skill_name=None,
            demand_level=None,
            avg_salary_min=entry["avg_salary_min"],
            avg_salary_max=entry["avg_salary_max"],
            years_range=entry["years_range"],
            updated_at=now,
        ))
        count += 1

    # 스킬 수요 데이터
    for entry in SKILL_DEMAND:
        db.add(MarketData(
            id=uuid.uuid4(),
            job_category=entry["job_category"],
            skill_name=entry["skill_name"],
            demand_level=entry["demand_level"],
            avg_salary_min=None,
            avg_salary_max=None,
            years_range=None,
            updated_at=now,
        ))
        count += 1

    await db.commit()
    return count


def get_salary_range(job_category: str, years: int) -> tuple[int, int]:
    """직군/연차 기반 기본 연봉 범위 (만원 단위) 반환"""
    yr = _get_years_range(years)
    for entry in SALARY_DATA:
        if entry["job_category"] == job_category and entry["years_range"] == yr:
            return entry["avg_salary_min"], entry["avg_salary_max"]
    # 기타 카테고리 폴백
    for entry in SALARY_DATA:
        if entry["job_category"] == "other" and entry["years_range"] == yr:
            return entry["avg_salary_min"], entry["avg_salary_max"]
    return 3000, 5000


def get_skill_demand(job_category: str, skill_name: str) -> int:
    """스킬의 시장 수요 레벨 반환 (1-10, 기본값 5)"""
    skill_lower = skill_name.lower()
    for entry in SKILL_DEMAND:
        if entry["job_category"] == job_category and entry["skill_name"].lower() == skill_lower:
            return entry["demand_level"]
    # 직군 무관 매치
    for entry in SKILL_DEMAND:
        if entry["skill_name"].lower() == skill_lower:
            return entry["demand_level"]
    return 5
