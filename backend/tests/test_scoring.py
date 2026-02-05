"""
스코어링 엔진 단위 테스트
- CareerScorer의 5대 영역 점수 계산 검증
- 다양한 입력 데이터 시나리오
"""

import pytest
from app.services.scoring import CareerScorer


# ── Fixtures ──

def make_linkedin_data(**overrides) -> dict:
    data = {
        "platform": "linkedin",
        "name": "홍길동",
        "current_title": "Senior Software Engineer",
        "skills": ["Python", "JavaScript", "React", "AWS", "Docker"],
        "experience": [
            {"title": "Senior Engineer", "company": "테크사", "duration": "3년"},
            {"title": "Junior Engineer", "company": "스타트업", "duration": "2년"},
        ],
        "education": [{"school": "서울대", "degree": "학사", "field": "컴퓨터공학"}],
        "certifications": ["AWS Solutions Architect"],
        "recommendation_count": 3,
        "data_quality": "high",
    }
    data.update(overrides)
    return data


def make_github_data(**overrides) -> dict:
    data = {
        "platform": "github",
        "name": "honggildong",
        "followers": 150,
        "public_repos": 25,
        "top_languages": ["Python", "TypeScript", "Go"],
        "pinned_repos": [
            {"name": "my-project", "stars": 50, "language": "Python"},
            {"name": "tool-kit", "stars": 30, "language": "TypeScript"},
        ],
        "contribution_summary": "Active daily contributor with consistent commit history",
        "data_quality": "high",
    }
    data.update(overrides)
    return data


def make_velog_data(**overrides) -> dict:
    data = {
        "platform": "velog",
        "name": "홍길동",
        "total_posts": 30,
        "recent_posts": [
            {"title": f"포스트 {i}", "date": "2026-01-01", "tags": ["tech"]}
            for i in range(6)
        ],
        "posting_frequency": "weekly posting schedule",
        "series": ["React 시리즈", "Python 시리즈"],
        "data_quality": "medium",
    }
    data.update(overrides)
    return data


# ── Tests ──

class TestCareerScorer:
    """CareerScorer 기본 동작 검증"""

    def test_all_scores_range_0_to_100(self):
        scorer = CareerScorer(
            sources_data=[make_linkedin_data(), make_github_data()],
            job_category="dev",
            years_of_experience=5,
        )
        result = scorer.calculate_all()

        for key in ["expertise", "influence", "consistency", "marketability", "potential", "total"]:
            assert 0 <= result[key] <= 100, f"{key} = {result[key]} is out of range"

    def test_empty_sources_returns_low_scores(self):
        scorer = CareerScorer(
            sources_data=[],
            job_category="dev",
            years_of_experience=0,
        )
        result = scorer.calculate_all()

        assert result["total"] < 30
        assert result["analysis_accuracy"] == 30.0

    def test_rich_data_returns_higher_scores(self):
        rich_scorer = CareerScorer(
            sources_data=[make_linkedin_data(), make_github_data(), make_velog_data()],
            job_category="dev",
            years_of_experience=8,
        )
        poor_scorer = CareerScorer(
            sources_data=[{"platform": "other", "data_quality": "low"}],
            job_category="dev",
            years_of_experience=1,
        )

        rich = rich_scorer.calculate_all()
        poor = poor_scorer.calculate_all()

        assert rich["total"] > poor["total"]
        assert rich["expertise"] > poor["expertise"]

    def test_expertise_skill_count_matters(self):
        few_skills = CareerScorer(
            sources_data=[make_linkedin_data(skills=["Python"])],
            job_category="dev",
            years_of_experience=5,
        )
        many_skills = CareerScorer(
            sources_data=[make_linkedin_data(skills=[
                "Python", "JavaScript", "React", "AWS", "Docker",
                "Kubernetes", "PostgreSQL", "Redis", "Go", "TypeScript",
            ])],
            job_category="dev",
            years_of_experience=5,
        )

        assert many_skills.score_expertise() > few_skills.score_expertise()

    def test_influence_followers_matter(self):
        low_influence = CareerScorer(
            sources_data=[make_github_data(followers=5, public_repos=2)],
            job_category="dev",
            years_of_experience=3,
        )
        high_influence = CareerScorer(
            sources_data=[make_github_data(followers=500, public_repos=50)],
            job_category="dev",
            years_of_experience=3,
        )

        assert high_influence.score_influence() > low_influence.score_influence()

    def test_consistency_posting_frequency(self):
        no_posts = CareerScorer(
            sources_data=[make_velog_data(
                total_posts=0,
                recent_posts=[],
                posting_frequency="",
                series=[],
            )],
            job_category="dev",
            years_of_experience=3,
        )
        active_posts = CareerScorer(
            sources_data=[make_velog_data()],
            job_category="dev",
            years_of_experience=3,
        )

        assert active_posts.score_consistency() > no_posts.score_consistency()

    def test_marketability_high_demand_skills(self):
        low_demand = CareerScorer(
            sources_data=[make_linkedin_data(skills=["COBOL", "Fortran"])],
            job_category="dev",
            years_of_experience=5,
        )
        high_demand = CareerScorer(
            sources_data=[make_linkedin_data(skills=["AI/ML", "LLM", "Python", "AWS"])],
            job_category="dev",
            years_of_experience=5,
        )

        assert high_demand.score_marketability() > low_demand.score_marketability()

    def test_analysis_accuracy_reflects_data_quality(self):
        high_quality = CareerScorer(
            sources_data=[
                make_linkedin_data(data_quality="high"),
                make_github_data(data_quality="high"),
            ],
            job_category="dev",
            years_of_experience=5,
        )
        low_quality = CareerScorer(
            sources_data=[{"platform": "other", "data_quality": "low"}],
            job_category="dev",
            years_of_experience=5,
        )

        high_result = high_quality.calculate_all()
        low_result = low_quality.calculate_all()

        assert high_result["analysis_accuracy"] > low_result["analysis_accuracy"]

    def test_total_is_weighted_average(self):
        scorer = CareerScorer(
            sources_data=[make_linkedin_data()],
            job_category="dev",
            years_of_experience=5,
        )
        result = scorer.calculate_all()

        weights = {
            "expertise": 0.25,
            "influence": 0.20,
            "consistency": 0.20,
            "marketability": 0.20,
            "potential": 0.15,
        }
        expected_total = sum(result[k] * weights[k] for k in weights)

        assert abs(result["total"] - round(expected_total, 1)) < 0.2

    def test_different_job_categories(self):
        dev_scorer = CareerScorer(
            sources_data=[make_linkedin_data(skills=["Figma", "UI/UX", "Product Design"])],
            job_category="dev",
            years_of_experience=5,
        )
        design_scorer = CareerScorer(
            sources_data=[make_linkedin_data(skills=["Figma", "UI/UX", "Product Design"])],
            job_category="design",
            years_of_experience=5,
        )

        # 디자인 스킬을 가진 사람은 디자인 직군에서 시장성이 같거나 더 높아야 함
        assert design_scorer.score_marketability() >= dev_scorer.score_marketability()
