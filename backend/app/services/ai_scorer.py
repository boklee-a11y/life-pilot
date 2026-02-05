"""
Claude API 기반 정성 분석 보정 + 인사이트 생성
- 규칙 기반 정량 점수에 대한 정성 보정 (-10 ~ +10)
- 영역별 강점/약점 인사이트 자연어 생성
- 예상 연봉 범위 보정
"""

import json
import logging

from anthropic import AsyncAnthropic

from app.core.config import settings
from app.services.market_seed import get_salary_range

logger = logging.getLogger(__name__)

client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

SCORING_SYSTEM_PROMPT = """You are a career analysis expert who evaluates professionals across 5 key areas.
You provide calibration adjustments to rule-based scores and generate actionable insights.
Always respond in valid JSON format. Write insights in Korean (한국어)."""

SCORING_USER_PROMPT = """Based on the following career data, provide score adjustments and insights.

== User Profile ==
직군: {job_category}
경력: {years}년

== Collected Data Summary ==
보유 스킬: {skills}
경력 수: {exp_count}개 회사/역할
프로젝트/레포: {proj_count}개
블로그 포스팅: {post_count}개
팔로워: {followers}명
추천서: {rec_count}개
자격증: {cert_count}개
활용 플랫폼: {platforms}

== Rule-based Scores (0-100) ==
전문성 (Expertise): {expertise}
영향력 (Influence): {influence}
지속성 (Consistency): {consistency}
시장성 (Marketability): {marketability}
성장성 (Potential): {potential}
종합: {total}

== Detailed Source Data ==
{source_details}

Return JSON with this exact structure:
{{
  "adjustments": {{
    "expertise": <int between -10 and 10>,
    "influence": <int between -10 and 10>,
    "consistency": <int between -10 and 10>,
    "marketability": <int between -10 and 10>,
    "potential": <int between -10 and 10>
  }},
  "insights": {{
    "overall_summary": "2-3문장 종합 분석",
    "strengths": ["강점 1", "강점 2", "강점 3"],
    "weaknesses": ["약점 1", "약점 2"],
    "expertise_detail": "전문성 영역 상세 분석 (2문장)",
    "influence_detail": "영향력 영역 상세 분석 (2문장)",
    "consistency_detail": "지속성 영역 상세 분석 (2문장)",
    "marketability_detail": "시장성 영역 상세 분석 (2문장)",
    "potential_detail": "성장성 영역 상세 분석 (2문장)"
  }},
  "salary_adjustment_percent": <int between -15 and 15>,
  "market_position_percentile": <int between 1 and 99>
}}"""


async def get_ai_calibration(
    sources_data: list[dict],
    scores: dict,
    job_category: str,
    years: int,
) -> dict:
    """
    Claude API를 사용하여 정성 분석 보정 및 인사이트 생성

    Returns:
        {
            "adjustments": { area: int },
            "insights": { ... },
            "salary_adjustment_percent": int,
            "market_position_percentile": int,
        }
    """
    # 통합 데이터 집계
    all_skills = set()
    exp_count = 0
    proj_count = 0
    post_count = 0
    followers = 0
    rec_count = 0
    cert_count = 0
    platforms = set()
    source_details_parts = []

    for src in sources_data:
        if not src:
            continue
        platform = src.get("platform", "other")
        platforms.add(platform)

        for s in (src.get("skills") or []):
            if isinstance(s, str):
                all_skills.add(s)
        for lang in (src.get("top_languages") or []):
            if isinstance(lang, str):
                all_skills.add(lang)

        exp_count += len(src.get("experience") or [])
        proj_count += len(src.get("projects") or []) + len(src.get("pinned_repos") or [])
        post_count += int(src.get("total_posts") or 0)
        followers += int(src.get("followers") or 0)
        rec_count += int(src.get("recommendation_count") or 0)
        cert_count += len(src.get("certifications") or [])

        # Summarize each source (truncated)
        summary = json.dumps(src, ensure_ascii=False, default=str)[:1500]
        source_details_parts.append(f"[{platform}] {summary}")

    source_details = "\n\n".join(source_details_parts)[:8000]

    prompt = SCORING_USER_PROMPT.format(
        job_category=job_category,
        years=years,
        skills=", ".join(sorted(all_skills)[:30]) or "정보 없음",
        exp_count=exp_count,
        proj_count=proj_count,
        post_count=post_count,
        followers=followers,
        rec_count=rec_count,
        cert_count=cert_count,
        platforms=", ".join(sorted(platforms)) or "없음",
        expertise=scores.get("expertise", 0),
        influence=scores.get("influence", 0),
        consistency=scores.get("consistency", 0),
        marketability=scores.get("marketability", 0),
        potential=scores.get("potential", 0),
        total=scores.get("total", 0),
        source_details=source_details,
    )

    if not settings.ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not set, returning default calibration")
        return _generate_default_calibration(scores, job_category, years)

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            system=SCORING_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text

        # Extract JSON
        json_str = response_text
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]

        result = json.loads(json_str.strip())

        # Validate adjustments range
        for area in ["expertise", "influence", "consistency", "marketability", "potential"]:
            adj = result.get("adjustments", {}).get(area, 0)
            result["adjustments"][area] = max(-10, min(10, int(adj)))

        return result

    except Exception as e:
        logger.error(f"AI calibration failed: {e}")
        return _generate_default_calibration(scores, job_category, years)


def _generate_default_calibration(scores: dict, job_category: str, years: int) -> dict:
    """AI 호출 실패 시 기본 보정값"""
    total = scores.get("total", 50)

    if total >= 70:
        position = 75
    elif total >= 50:
        position = 50
    else:
        position = 30

    return {
        "adjustments": {
            "expertise": 0,
            "influence": 0,
            "consistency": 0,
            "marketability": 0,
            "potential": 0,
        },
        "insights": {
            "overall_summary": "데이터를 기반으로 한 기본 분석 결과입니다. Claude API를 연동하면 더 정교한 인사이트를 받을 수 있습니다.",
            "strengths": ["프로필 데이터를 등록하여 분석을 시작했습니다"],
            "weaknesses": ["더 많은 데이터 소스를 연동하면 분석 정확도가 높아집니다"],
            "expertise_detail": "보유 스킬과 경력 데이터를 기반으로 전문성을 평가했습니다.",
            "influence_detail": "온라인 활동과 팔로워 데이터를 기반으로 영향력을 평가했습니다.",
            "consistency_detail": "활동 빈도와 포스팅 주기를 기반으로 지속성을 평가했습니다.",
            "marketability_detail": "보유 스킬의 시장 수요를 기반으로 시장성을 평가했습니다.",
            "potential_detail": "최신 기술 비율과 학습 이력을 기반으로 성장성을 평가했습니다.",
        },
        "salary_adjustment_percent": 0,
        "market_position_percentile": position,
    }


def calculate_salary(
    base_scores: dict,
    job_category: str,
    years: int,
    salary_adjustment_percent: int = 0,
) -> tuple[int, int]:
    """
    스코어 기반 예상 연봉 범위 산출 (만원 단위)

    기본 연봉 범위에서 종합 점수에 따라 범위 내 위치를 결정하고,
    AI 보정 퍼센트를 적용합니다.
    """
    base_min, base_max = get_salary_range(job_category, years)
    salary_range = base_max - base_min

    total_score = base_scores.get("total", 50)

    # 종합 점수에 따라 범위 내 위치 결정 (50점 = 중앙)
    score_factor = total_score / 100

    estimated_mid = base_min + salary_range * score_factor
    # 연봉 범위는 ±10% 정도
    estimated_min = int(estimated_mid * 0.9)
    estimated_max = int(estimated_mid * 1.1)

    # AI 보정 적용
    if salary_adjustment_percent:
        adj_factor = 1 + salary_adjustment_percent / 100
        estimated_min = int(estimated_min * adj_factor)
        estimated_max = int(estimated_max * adj_factor)

    # 최소값이 기본 최소보다 낮지 않도록
    estimated_min = max(estimated_min, int(base_min * 0.8))

    return estimated_min, estimated_max
