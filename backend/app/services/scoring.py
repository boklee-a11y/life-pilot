"""
5대 영역 규칙 기반 스코어링 엔진
- 전문성 (Expertise): 스킬 수 × 희소성, 경력 깊이, 자격증
- 영향력 (Influence): 팔로워, 블로그 지표, 오픈소스 기여, 추천서
- 지속성 (Consistency): 활동 빈도, 포스팅 주기, 근속 연수
- 시장성 (Marketability): 보유 스킬의 시장 수요, 직군 트렌드
- 성장성 (Potential): 최신 기술 비율, 최근 활동 추세, 학습 패턴
"""

import logging
from typing import Any

from app.services.market_seed import get_skill_demand

logger = logging.getLogger(__name__)


def _safe_int(val: Any, default: int = 0) -> int:
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _safe_list(val: Any) -> list:
    if isinstance(val, list):
        return val
    return []


def _clamp(value: float, min_val: float = 0, max_val: float = 100) -> float:
    return max(min_val, min(max_val, value))


class CareerScorer:
    """
    parsed_data 리스트와 유저 정보를 기반으로 5대 영역 점수를 산출합니다.
    """

    def __init__(
        self,
        sources_data: list[dict],
        job_category: str,
        years_of_experience: int,
    ):
        self.sources = sources_data
        self.job_category = job_category or "other"
        self.years = years_of_experience or 0
        self._aggregate = self._build_aggregate()

    def _build_aggregate(self) -> dict:
        """모든 소스 데이터를 하나의 통합 프로필로 합침"""
        agg: dict[str, Any] = {
            "skills": set(),
            "experience_items": [],
            "education_items": [],
            "certifications": [],
            "projects": [],
            "post_count": 0,
            "followers": 0,
            "public_repos": 0,
            "stars": 0,
            "recommendation_count": 0,
            "recent_posts": [],
            "contribution_summary": "",
            "top_languages": set(),
            "posting_frequency": "",
            "series_count": 0,
            "platforms_used": set(),
            "data_qualities": [],
        }

        for src in self.sources:
            if not src:
                continue

            platform = src.get("platform", "other")
            agg["platforms_used"].add(platform)
            dq = src.get("data_quality", "low")
            agg["data_qualities"].append(dq)

            # Skills
            for skill in _safe_list(src.get("skills")):
                if isinstance(skill, str):
                    agg["skills"].add(skill)
            for lang in _safe_list(src.get("top_languages")):
                if isinstance(lang, str):
                    agg["skills"].add(lang)
                    agg["top_languages"].add(lang)

            # Experience
            for exp in _safe_list(src.get("experience")):
                agg["experience_items"].append(exp)

            # Education
            for edu in _safe_list(src.get("education")):
                agg["education_items"].append(edu)

            # Certifications
            for cert in _safe_list(src.get("certifications")):
                agg["certifications"].append(cert)

            # Projects
            for proj in _safe_list(src.get("projects")):
                agg["projects"].append(proj)
            for repo in _safe_list(src.get("pinned_repos")):
                agg["projects"].append(repo)

            # Quantitative
            agg["followers"] += _safe_int(src.get("followers"))
            agg["public_repos"] += _safe_int(src.get("public_repos"))
            agg["recommendation_count"] += _safe_int(src.get("recommendation_count"))
            agg["post_count"] += _safe_int(src.get("total_posts"))

            # Stars from pinned repos
            for repo in _safe_list(src.get("pinned_repos")):
                agg["stars"] += _safe_int(repo.get("stars") if isinstance(repo, dict) else 0)

            # Posts
            for post in _safe_list(src.get("recent_posts")):
                agg["recent_posts"].append(post)

            # Contribution
            cs = src.get("contribution_summary")
            if cs:
                agg["contribution_summary"] += f" {cs}"

            # Posting frequency
            pf = src.get("posting_frequency")
            if pf:
                agg["posting_frequency"] += f" {pf}"

            # Series
            agg["series_count"] += len(_safe_list(src.get("series")))

            # Generic quantitative_metrics
            qm = src.get("quantitative_metrics")
            if isinstance(qm, dict):
                agg["followers"] += _safe_int(qm.get("followers"))
                agg["post_count"] += _safe_int(qm.get("post_count"))

        return agg

    def score_expertise(self) -> float:
        """
        전문성 점수:
        - 스킬 수 × 희소성 가중치 (30%)
        - 프로젝트/경력 깊이 (30%)
        - 경력 연차 (20%)
        - 자격증 (20%)
        """
        agg = self._aggregate

        # 스킬 점수: 스킬 수 × 평균 수요 레벨
        skills = list(agg["skills"])
        skill_count = len(skills)
        if skill_count > 0:
            avg_demand = sum(
                get_skill_demand(self.job_category, s) for s in skills
            ) / skill_count
            # 스킬 10개 이상이면 만점 구간
            skill_score = min(skill_count / 10, 1.0) * 50 + (avg_demand / 10) * 50
        else:
            skill_score = 0

        # 프로젝트/경력 깊이
        exp_count = len(agg["experience_items"])
        proj_count = len(agg["projects"])
        depth_score = min((exp_count * 15 + proj_count * 10), 100)

        # 경력 연차 (15년이면 100)
        years_score = min(self.years / 15 * 100, 100)

        # 자격증
        cert_count = len(agg["certifications"])
        cert_score = min(cert_count * 25, 100)

        total = skill_score * 0.30 + depth_score * 0.30 + years_score * 0.20 + cert_score * 0.20
        return round(_clamp(total), 1)

    def score_influence(self) -> float:
        """
        영향력 점수:
        - 팔로워/구독자 (30%)
        - 블로그 포스팅 지표 (25%)
        - 오픈소스 기여 (25%)
        - 추천서/보증 (20%)
        """
        agg = self._aggregate

        # 팔로워 (1000명이면 만점)
        follower_score = min(agg["followers"] / 1000 * 100, 100)

        # 블로그 포스팅 (50개 이상이면 만점)
        post_score = min(agg["post_count"] / 50 * 100, 100)

        # 오픈소스: repos + stars
        repo_score = min(agg["public_repos"] / 30 * 50, 50)
        star_score = min(agg["stars"] / 100 * 50, 50)
        oss_score = repo_score + star_score

        # 추천서 (5개면 만점)
        rec_score = min(agg["recommendation_count"] / 5 * 100, 100)

        total = follower_score * 0.30 + post_score * 0.25 + oss_score * 0.25 + rec_score * 0.20
        return round(_clamp(total), 1)

    def score_consistency(self) -> float:
        """
        지속성 점수:
        - 활동 빈도/커밋 (35%)
        - 블로그 포스팅 주기 (30%)
        - 근속 연수/경력 연속성 (20%)
        - 시리즈/연속 학습 (15%)
        """
        agg = self._aggregate

        # 활동 빈도 (contribution_summary 텍스트 분석)
        contrib = agg["contribution_summary"].lower()
        if any(kw in contrib for kw in ["daily", "매일", "every day", "active"]):
            activity_score = 90
        elif any(kw in contrib for kw in ["weekly", "주간", "regular", "consistent"]):
            activity_score = 70
        elif any(kw in contrib for kw in ["monthly", "월간"]):
            activity_score = 50
        elif contrib.strip():
            activity_score = 40
        else:
            activity_score = 10 if agg["public_repos"] > 0 else 0

        # 블로그 포스팅 주기
        freq = agg["posting_frequency"].lower()
        recent_count = len(agg["recent_posts"])
        if any(kw in freq for kw in ["weekly", "주간", "매주"]):
            posting_score = 85
        elif any(kw in freq for kw in ["bi-weekly", "격주", "2주"]):
            posting_score = 70
        elif any(kw in freq for kw in ["monthly", "월간", "매월"]):
            posting_score = 55
        elif recent_count >= 5:
            posting_score = 50
        elif recent_count > 0:
            posting_score = 30
        else:
            posting_score = 0

        # 근속 연수 (경력 연속성)
        exp_count = len(agg["experience_items"])
        if self.years >= 5 and exp_count <= 3:
            tenure_score = 80  # 적은 이직 = 높은 근속
        elif self.years >= 3:
            tenure_score = 60
        elif self.years >= 1:
            tenure_score = 40
        else:
            tenure_score = 20

        # 시리즈/연속 학습
        series_score = min(agg["series_count"] * 20, 100)

        total = (
            activity_score * 0.35
            + posting_score * 0.30
            + tenure_score * 0.20
            + series_score * 0.15
        )
        return round(_clamp(total), 1)

    def score_marketability(self) -> float:
        """
        시장성 점수:
        - 보유 스킬의 평균 시장 수요 (50%)
        - 고수요 스킬 보유 비율 (30%)
        - 플랫폼 다양성 (20%)
        """
        agg = self._aggregate
        skills = list(agg["skills"])

        if not skills:
            # 스킬 정보 없으면 기본값
            return round(_clamp(30 + self.years * 2), 1)

        # 평균 시장 수요
        demands = [get_skill_demand(self.job_category, s) for s in skills]
        avg_demand = sum(demands) / len(demands)
        demand_score = (avg_demand / 10) * 100

        # 고수요 스킬 (8 이상) 비율
        high_demand_count = sum(1 for d in demands if d >= 8)
        high_demand_ratio = high_demand_count / len(skills)
        high_demand_score = high_demand_ratio * 100

        # 플랫폼 다양성 (4개 이상이면 만점)
        platform_count = len(agg["platforms_used"])
        platform_score = min(platform_count / 4 * 100, 100)

        total = demand_score * 0.50 + high_demand_score * 0.30 + platform_score * 0.20
        return round(_clamp(total), 1)

    def score_potential(self) -> float:
        """
        성장성 점수:
        - 최신/고수요 기술 비율 (35%)
        - 최근 활동 추세 (30%)
        - 학습/교육 이력 (20%)
        - 데이터 품질 (정보 공개 적극성) (15%)
        """
        agg = self._aggregate
        skills = list(agg["skills"])

        # 최신 기술 비율
        HIGH_DEMAND_SKILLS = {
            "ai/ml", "llm", "machine learning", "deep learning",
            "typescript", "rust", "go", "kubernetes", "next.js",
            "react", "flutter", "aws", "cloud", "devops", "figma",
            "product design", "data analysis", "growth hacking",
        }
        if skills:
            modern_count = sum(
                1 for s in skills if s.lower() in HIGH_DEMAND_SKILLS
            )
            modern_ratio = modern_count / len(skills)
            modern_score = min(modern_ratio * 200, 100)  # 50% 이상이면 만점
        else:
            modern_score = 20

        # 최근 활동 추세 (최근 게시글 수)
        recent_posts = agg["recent_posts"]
        if len(recent_posts) >= 10:
            trend_score = 90
        elif len(recent_posts) >= 5:
            trend_score = 70
        elif len(recent_posts) >= 2:
            trend_score = 50
        elif len(recent_posts) >= 1:
            trend_score = 30
        else:
            trend_score = 10

        # 학습/교육 이력
        edu_count = len(agg["education_items"])
        cert_count = len(agg["certifications"])
        learning_score = min((edu_count * 20 + cert_count * 25), 100)

        # 데이터 품질 (정보 공개 적극성)
        qualities = agg["data_qualities"]
        if qualities:
            quality_map = {"high": 100, "medium": 60, "low": 30}
            avg_quality = sum(quality_map.get(q, 30) for q in qualities) / len(qualities)
        else:
            avg_quality = 20

        total = (
            modern_score * 0.35
            + trend_score * 0.30
            + learning_score * 0.20
            + avg_quality * 0.15
        )
        return round(_clamp(total), 1)

    def calculate_all(self) -> dict:
        """5대 영역 전체 스코어 + 종합 점수 계산"""
        scores = {
            "expertise": self.score_expertise(),
            "influence": self.score_influence(),
            "consistency": self.score_consistency(),
            "marketability": self.score_marketability(),
            "potential": self.score_potential(),
        }

        # 종합 점수 (가중 평균)
        weights = {
            "expertise": 0.25,
            "influence": 0.20,
            "consistency": 0.20,
            "marketability": 0.20,
            "potential": 0.15,
        }
        total = sum(scores[k] * weights[k] for k in scores)
        scores["total"] = round(total, 1)

        # 분석 정확도 (데이터 품질 기반)
        qualities = self._aggregate["data_qualities"]
        if qualities:
            quality_map = {"high": 90, "medium": 65, "low": 40}
            accuracy = sum(quality_map.get(q, 40) for q in qualities) / len(qualities)
            # 소스 수에 따른 보너스 (최대 10%)
            source_bonus = min(len(self.sources) * 3, 10)
            scores["analysis_accuracy"] = round(min(accuracy + source_bonus, 100), 1)
        else:
            scores["analysis_accuracy"] = 30.0

        return scores
