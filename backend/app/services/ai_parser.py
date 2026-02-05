"""
Claude API를 활용한 스크래핑 데이터 구조화 서비스
- 스크래핑된 비정형 텍스트 → 구조화된 JSON
- 플랫폼별 최적화된 프롬프트
"""

import json
import logging

from anthropic import AsyncAnthropic

from app.core.config import settings

logger = logging.getLogger(__name__)

client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a career data extraction specialist.
You analyze scraped web page content and extract structured career-related information.
Always respond in valid JSON format. Be thorough but only include information that is actually present in the data.
If certain fields cannot be determined, use null instead of guessing."""

PLATFORM_PROMPTS = {
    "linkedin": """Analyze this LinkedIn profile page content and extract structured data.

Return JSON with this exact structure:
{
  "platform": "linkedin",
  "name": "string or null",
  "current_title": "string or null",
  "company": "string or null",
  "location": "string or null",
  "headline": "string or null",
  "skills": ["list of skills found"],
  "experience": [
    {
      "title": "string",
      "company": "string",
      "duration": "string or null",
      "description": "string or null"
    }
  ],
  "education": [
    {
      "school": "string",
      "degree": "string or null",
      "field": "string or null",
      "years": "string or null"
    }
  ],
  "certifications": ["list of certifications"],
  "recommendation_count": "number or null",
  "activity_summary": "brief summary of recent activity",
  "data_quality": "high/medium/low"
}""",

    "github": """Analyze this GitHub profile page content and extract structured data.

Return JSON with this exact structure:
{
  "platform": "github",
  "name": "string or null",
  "username": "string or null",
  "bio": "string or null",
  "location": "string or null",
  "company": "string or null",
  "followers": "number or null",
  "following": "number or null",
  "public_repos": "number or null",
  "pinned_repos": [
    {
      "name": "string",
      "description": "string or null",
      "language": "string or null",
      "stars": "number or null"
    }
  ],
  "top_languages": ["list of programming languages"],
  "contribution_summary": "string describing contribution activity",
  "notable_projects": ["list of notable project names"],
  "data_quality": "high/medium/low"
}""",

    "velog": """Analyze this Velog blog profile page content and extract structured data.

Return JSON with this exact structure:
{
  "platform": "velog",
  "name": "string or null",
  "username": "string or null",
  "bio": "string or null",
  "total_posts": "number or null",
  "recent_posts": [
    {
      "title": "string",
      "date": "string or null",
      "tags": ["list of tags"],
      "brief": "string or null"
    }
  ],
  "main_topics": ["list of main writing topics"],
  "posting_frequency": "string describing how often they post",
  "series": ["list of series names"],
  "data_quality": "high/medium/low"
}""",

    "tistory": """Analyze this Tistory blog page content and extract structured data.

Return JSON with this exact structure:
{
  "platform": "tistory",
  "blog_name": "string or null",
  "author": "string or null",
  "total_posts": "number or null",
  "categories": ["list of categories"],
  "recent_posts": [
    {
      "title": "string",
      "date": "string or null",
      "category": "string or null"
    }
  ],
  "main_topics": ["list of main writing topics"],
  "posting_frequency": "string describing how often they post",
  "data_quality": "high/medium/low"
}""",
}

GENERIC_PROMPT = """Analyze this web page content and extract any career-related structured data.
This page could be a portfolio, personal blog, resume page, or any professional profile.

Return JSON with this exact structure:
{
  "platform": "other",
  "page_type": "portfolio/blog/resume/profile/other",
  "name": "string or null",
  "role_or_title": "string or null",
  "skills": ["list of skills found"],
  "projects": [
    {
      "name": "string",
      "description": "string or null",
      "technologies": ["list of tech used"]
    }
  ],
  "experience_summary": "string or null",
  "education": ["list of education items"],
  "activity_summary": "brief summary of what this page shows",
  "quantitative_metrics": {
    "followers": "number or null",
    "post_count": "number or null",
    "project_count": "number or null"
  },
  "data_quality": "high/medium/low"
}"""


async def parse_with_ai(
    scraped_text: str, platform: str, url: str
) -> dict:
    """
    Claude API를 사용하여 스크래핑된 텍스트를 구조화된 JSON으로 변환

    Args:
        scraped_text: 스크래핑 후 정제된 텍스트
        platform: 감지된 플랫폼
        url: 원본 URL

    Returns:
        구조화된 딕셔너리 (parsed_data)
    """
    if not settings.ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not set, returning mock data")
        return _generate_mock_data(platform, url)

    prompt = PLATFORM_PROMPTS.get(platform, GENERIC_PROMPT)

    user_message = f"""URL: {url}
Platform: {platform}

=== PAGE CONTENT START ===
{scraped_text[:12000]}
=== PAGE CONTENT END ===

{prompt}"""

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        response_text = response.content[0].text

        # Extract JSON from response (handle markdown code blocks)
        json_str = response_text
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]

        parsed = json.loads(json_str.strip())
        parsed["profile_url"] = url
        return parsed

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        return {
            "platform": platform,
            "profile_url": url,
            "raw_response": response_text if "response_text" in dir() else "",
            "parse_error": str(e),
            "data_quality": "low",
        }
    except Exception as e:
        logger.error(f"Claude API call failed: {e}")
        return _generate_mock_data(platform, url)


def _generate_mock_data(platform: str, url: str) -> dict:
    """API 키가 없을 때 테스트용 목 데이터 생성"""
    return {
        "platform": platform,
        "profile_url": url,
        "name": None,
        "data_quality": "low",
        "_mock": True,
        "_message": "ANTHROPIC_API_KEY not configured. Set it in .env for real analysis.",
    }
