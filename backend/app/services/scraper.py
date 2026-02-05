"""
URL 스크래핑 서비스
- 알려진 플랫폼: 최적화된 스크래핑 전략
- 기타 URL: 범용 Playwright 스크래핑
"""

import re
import logging
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

PLATFORM_PATTERNS = {
    "linkedin": r"linkedin\.com/in/",
    "github": r"github\.com/",
    "velog": r"velog\.io/@",
    "tistory": r"\.tistory\.com",
    "dribbble": r"dribbble\.com/",
    "behance": r"behance\.net/",
    "notion": r"notion\.so/",
    "medium": r"medium\.com/@?",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}


def detect_platform(url: str) -> str:
    for platform, pattern in PLATFORM_PATTERNS.items():
        if re.search(pattern, url):
            return platform
    return "other"


async def scrape_url(url: str, platform: str | None = None) -> dict:
    """
    URL을 스크래핑하고 정제된 텍스트를 반환합니다.

    Returns:
        {
            "platform": str,
            "url": str,
            "raw_html": str,
            "cleaned_text": str,
            "title": str,
            "success": bool,
            "error": str | None,
        }
    """
    detected_platform = platform or detect_platform(url)

    try:
        if detected_platform == "linkedin":
            return await _scrape_with_playwright(url, detected_platform)
        else:
            result = await _scrape_with_httpx(url, detected_platform)
            if not result["success"] or len(result["cleaned_text"]) < 100:
                # Fallback to Playwright for JS-rendered pages
                return await _scrape_with_playwright(url, detected_platform)
            return result
    except Exception as e:
        logger.error(f"Scraping failed for {url}: {e}")
        return {
            "platform": detected_platform,
            "url": url,
            "raw_html": "",
            "cleaned_text": "",
            "title": "",
            "success": False,
            "error": str(e),
        }


async def _scrape_with_httpx(url: str, platform: str) -> dict:
    """httpx를 사용한 정적 페이지 스크래핑"""
    async with httpx.AsyncClient(
        headers=HEADERS, follow_redirects=True, timeout=30.0
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        html = response.text

    cleaned_text, title = _extract_text(html, platform)

    return {
        "platform": platform,
        "url": url,
        "raw_html": html[:50000],  # Limit stored HTML
        "cleaned_text": cleaned_text,
        "title": title,
        "success": True,
        "error": None,
    }


async def _scrape_with_playwright(url: str, platform: str) -> dict:
    """Playwright를 사용한 동적 페이지 스크래핑"""
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=HEADERS["User-Agent"],
                locale="ko-KR",
            )
            page = await context.new_page()

            await page.goto(url, wait_until="networkidle", timeout=30000)
            # Extra wait for dynamic content
            await page.wait_for_timeout(2000)

            html = await page.content()
            title = await page.title()

            await browser.close()

        cleaned_text, _ = _extract_text(html, platform)

        return {
            "platform": platform,
            "url": url,
            "raw_html": html[:50000],
            "cleaned_text": cleaned_text,
            "title": title,
            "success": True,
            "error": None,
        }
    except Exception as e:
        logger.error(f"Playwright scraping failed for {url}: {e}")
        return {
            "platform": platform,
            "url": url,
            "raw_html": "",
            "cleaned_text": "",
            "title": "",
            "success": False,
            "error": f"Playwright error: {str(e)}",
        }


def _extract_text(html: str, platform: str) -> tuple[str, str]:
    """HTML에서 의미있는 텍스트를 추출합니다."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove script, style, nav, footer
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    # Platform-specific extraction
    if platform == "github":
        return _extract_github(soup), title
    elif platform == "velog":
        return _extract_velog(soup), title
    elif platform == "linkedin":
        return _extract_linkedin(soup), title

    # Generic extraction
    main_content = soup.find("main") or soup.find("article") or soup.find("body")
    if main_content:
        text = main_content.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    # Clean up excessive whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)[:15000], title


def _extract_github(soup: BeautifulSoup) -> str:
    """GitHub 프로필 페이지에서 핵심 정보 추출"""
    sections = []

    # Profile info
    profile = soup.find("div", class_=re.compile("vcard|h-card|js-profile"))
    if profile:
        sections.append("=== PROFILE ===")
        sections.append(profile.get_text(separator="\n", strip=True))

    # Pinned repos
    pinned = soup.find_all("div", class_=re.compile("pinned|js-pinned"))
    if pinned:
        sections.append("\n=== PINNED REPOSITORIES ===")
        for repo in pinned:
            sections.append(repo.get_text(separator=" ", strip=True))

    # Contribution graph info
    contrib = soup.find("div", class_=re.compile("contrib|graph"))
    if contrib:
        sections.append("\n=== CONTRIBUTIONS ===")
        sections.append(contrib.get_text(separator="\n", strip=True))

    # Popular repos
    repos = soup.find_all("li", class_=re.compile("repo|source"))
    if repos:
        sections.append("\n=== REPOSITORIES ===")
        for repo in repos[:10]:
            sections.append(repo.get_text(separator=" ", strip=True))

    result = "\n".join(sections)
    if len(result) < 100:
        # Fallback to body text
        body = soup.find("body")
        result = body.get_text(separator="\n", strip=True) if body else ""

    return result[:15000]


def _extract_velog(soup: BeautifulSoup) -> str:
    """Velog 프로필에서 글 목록 추출"""
    sections = []

    # User info
    user_info = soup.find("div", class_=re.compile("user|profile"))
    if user_info:
        sections.append("=== PROFILE ===")
        sections.append(user_info.get_text(separator="\n", strip=True))

    # Post list
    posts = soup.find_all("div", class_=re.compile("post|card"))
    if posts:
        sections.append("\n=== POSTS ===")
        for post in posts[:20]:
            sections.append(post.get_text(separator=" ", strip=True))

    result = "\n".join(sections)
    if len(result) < 100:
        body = soup.find("body")
        result = body.get_text(separator="\n", strip=True) if body else ""

    return result[:15000]


def _extract_linkedin(soup: BeautifulSoup) -> str:
    """LinkedIn 공개 프로필에서 정보 추출"""
    body = soup.find("body")
    if body:
        return body.get_text(separator="\n", strip=True)[:15000]
    return ""
