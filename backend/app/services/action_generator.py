"""
Claude API 기반 개인화 액션 추천 엔진
- 5대 영역 스코어 + 프로필 데이터 기반
- 약점 보완 + 강점 극대화 2트랙
- 각 액션: 제목, 설명, 효과%, 대상 영역, 난이도, 기간, 태그, CTA
"""

import json
import uuid
import logging
from datetime import datetime, timezone
from uuid import UUID

from anthropic import AsyncAnthropic
from sqlalchemy import select, desc

from app.core.config import settings
from app.core.database import async_session
from app.models.user import User
from app.models.data_source import DataSource
from app.models.career_score import CareerScore
from app.models.action_recommendation import ActionRecommendation

logger = logging.getLogger(__name__)

client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

ACTION_SYSTEM_PROMPT = """You are a career growth strategist.
Based on career analysis data, generate actionable growth recommendations.
Each action should be specific, measurable, and achievable.
Always respond in valid JSON. Write all content in Korean (한국어)."""

ACTION_USER_PROMPT = """Based on the following career analysis, generate personalized growth actions.

== Profile ==
직군: {job_category}
경력: {years}년

== 5대 영역 스코어 (0-100) ==
전문성 (Expertise): {expertise}
영향력 (Influence): {influence}
지속성 (Consistency): {consistency}
시장성 (Marketability): {marketability}
성장성 (Potential): {potential}
종합: {total}

== 강점/약점 ==
강점: {strengths}
약점: {weaknesses}

== 보유 스킬 ==
{skills}

== 분석 인사이트 ==
{insights_summary}

Generate 5-8 specific action recommendations following BOTH strategies:
1. 약점 보완 (2-3 actions): Focus on weakest areas
2. 강점 극대화 (3-5 actions): Leverage strongest areas for maximum impact

Return JSON array:
{{
  "actions": [
    {{
      "title": "구체적인 액션 제목 (20자 이내)",
      "description": "액션의 상세 설명과 이유 (2-3문장)",
      "impact_percent": <1-15 사이 정수, 예상 가치 상승 효과>,
      "target_area": "<expertise|influence|consistency|marketability|potential>",
      "difficulty": "<easy|medium|hard>",
      "estimated_duration": "예상 소요 기간 (예: 2주, 1개월, 3개월)",
      "tags": ["태그1", "태그2"],
      "cta_label": "CTA 버튼 텍스트 (예: 학습 시작하기)",
      "cta_url": null,
      "strategy": "<weakness|strength>"
    }}
  ]
}}"""


async def generate_actions(user_id: UUID, score_id: UUID) -> list[dict]:
    """
    최신 스코어와 프로필 데이터를 기반으로 액션 추천을 생성합니다.
    """
    async with async_session() as db:
        # 유저 + 스코어 + 소스 조회
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return []

        score_result = await db.execute(
            select(CareerScore).where(CareerScore.id == score_id)
        )
        score = score_result.scalar_one_or_none()
        if not score:
            return []

        sources_result = await db.execute(
            select(DataSource).where(
                DataSource.user_id == user_id,
                DataSource.status == "completed",
                DataSource.parsed_data.isnot(None),
            )
        )
        sources = sources_result.scalars().all()

        # 스킬 수집
        all_skills = set()
        for src in sources:
            if src.parsed_data:
                for s in (src.parsed_data.get("skills") or []):
                    if isinstance(s, str):
                        all_skills.add(s)
                for lang in (src.parsed_data.get("top_languages") or []):
                    if isinstance(lang, str):
                        all_skills.add(lang)

        insights = score.ai_insights or {}

        prompt = ACTION_USER_PROMPT.format(
            job_category=user.job_category or "other",
            years=user.years_of_experience or 0,
            expertise=float(score.expertise_score or 0),
            influence=float(score.influence_score or 0),
            consistency=float(score.consistency_score or 0),
            marketability=float(score.marketability_score or 0),
            potential=float(score.potential_score or 0),
            total=float(score.total_score or 0),
            strengths=", ".join(insights.get("strengths", [])) or "정보 없음",
            weaknesses=", ".join(insights.get("weaknesses", [])) or "정보 없음",
            skills=", ".join(sorted(all_skills)[:30]) or "정보 없음",
            insights_summary=insights.get("overall_summary", ""),
        )

        # Claude API 호출
        actions_data = await _call_claude_for_actions(prompt)

        # DB에 저장
        now = datetime.now(timezone.utc)
        saved_actions = []

        for action in actions_data:
            rec = ActionRecommendation(
                id=uuid.uuid4(),
                user_id=user_id,
                score_id=score_id,
                title=action.get("title", "추천 액션"),
                description=action.get("description"),
                impact_percent=action.get("impact_percent"),
                target_area=action.get("target_area"),
                difficulty=action.get("difficulty"),
                estimated_duration=action.get("estimated_duration"),
                tags=action.get("tags", []),
                cta_label=action.get("cta_label"),
                cta_url=action.get("cta_url"),
                is_completed=False,
                is_bookmarked=False,
                created_at=now,
            )
            db.add(rec)
            saved_actions.append(rec)

        await db.commit()
        logger.info(f"Generated {len(saved_actions)} actions for user {user_id}")
        return actions_data


async def _call_claude_for_actions(prompt: str) -> list[dict]:
    """Claude API를 호출하여 액션 목록을 생성합니다."""
    if not settings.ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not set, returning default actions")
        return _generate_default_actions()

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=3000,
            system=ACTION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text

        json_str = response_text
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]

        result = json.loads(json_str.strip())
        actions = result.get("actions", [])

        # Validate
        valid_areas = {"expertise", "influence", "consistency", "marketability", "potential"}
        valid_difficulties = {"easy", "medium", "hard"}
        validated = []
        for a in actions:
            if a.get("target_area") not in valid_areas:
                a["target_area"] = "expertise"
            if a.get("difficulty") not in valid_difficulties:
                a["difficulty"] = "medium"
            a["impact_percent"] = max(1, min(15, int(a.get("impact_percent", 5))))
            validated.append(a)

        return validated

    except Exception as e:
        logger.error(f"Action generation failed: {e}")
        return _generate_default_actions()


def _generate_default_actions() -> list[dict]:
    """API 키 미설정 시 기본 액션 목록"""
    return [
        {
            "title": "기술 블로그 시작하기",
            "description": "주 1회 기술 블로그를 작성하여 학습 내용을 정리하고, 온라인 영향력을 키우세요. 꾸준한 글쓰기는 전문성과 영향력 모두를 높여줍니다.",
            "impact_percent": 8,
            "target_area": "influence",
            "difficulty": "medium",
            "estimated_duration": "지속",
            "tags": ["글쓰기", "브랜딩"],
            "cta_label": "블로그 시작하기",
            "cta_url": None,
            "strategy": "strength",
        },
        {
            "title": "오픈소스 프로젝트 기여",
            "description": "관심 있는 오픈소스 프로젝트에 기여하여 실무 경험과 커뮤니티 인지도를 동시에 높이세요.",
            "impact_percent": 10,
            "target_area": "expertise",
            "difficulty": "hard",
            "estimated_duration": "3개월",
            "tags": ["스킬업", "네트워킹"],
            "cta_label": "프로젝트 찾기",
            "cta_url": None,
            "strategy": "strength",
        },
        {
            "title": "사이드 프로젝트 완성",
            "description": "개인 프로젝트를 하나 완성하여 포트폴리오를 강화하세요. 기획부터 배포까지 경험이 시장성을 높여줍니다.",
            "impact_percent": 12,
            "target_area": "marketability",
            "difficulty": "hard",
            "estimated_duration": "2개월",
            "tags": ["스킬업", "포트폴리오"],
            "cta_label": "프로젝트 계획하기",
            "cta_url": None,
            "strategy": "weakness",
        },
        {
            "title": "온라인 강의 수강",
            "description": "최신 기술 트렌드에 맞는 온라인 강의를 수강하여 성장성을 높이세요. 수료증은 프로필에 추가할 수 있습니다.",
            "impact_percent": 6,
            "target_area": "potential",
            "difficulty": "easy",
            "estimated_duration": "1개월",
            "tags": ["스킬업", "자격증"],
            "cta_label": "강의 찾기",
            "cta_url": None,
            "strategy": "weakness",
        },
        {
            "title": "LinkedIn 프로필 최적화",
            "description": "LinkedIn 프로필의 헤드라인, 소개, 경력 설명을 최적화하여 리크루터 노출을 높이세요.",
            "impact_percent": 5,
            "target_area": "marketability",
            "difficulty": "easy",
            "estimated_duration": "1주",
            "tags": ["브랜딩", "채용"],
            "cta_label": "프로필 수정하기",
            "cta_url": None,
            "strategy": "weakness",
        },
    ]
