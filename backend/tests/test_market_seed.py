"""
시장 데이터 유틸리티 함수 테스트
"""

from app.services.market_seed import get_salary_range, get_skill_demand, _get_years_range


class TestGetYearsRange:
    def test_junior(self):
        assert _get_years_range(0) == "0-2"
        assert _get_years_range(2) == "0-2"

    def test_mid(self):
        assert _get_years_range(3) == "3-5"
        assert _get_years_range(5) == "3-5"

    def test_senior(self):
        assert _get_years_range(6) == "6-9"
        assert _get_years_range(9) == "6-9"

    def test_lead(self):
        assert _get_years_range(10) == "10-14"
        assert _get_years_range(14) == "10-14"

    def test_veteran(self):
        assert _get_years_range(15) == "15+"
        assert _get_years_range(25) == "15+"


class TestGetSalaryRange:
    def test_dev_junior(self):
        min_s, max_s = get_salary_range("dev", 1)
        assert min_s == 3200
        assert max_s == 4500

    def test_dev_senior(self):
        min_s, max_s = get_salary_range("dev", 8)
        assert min_s > 5000
        assert max_s > min_s

    def test_unknown_category_fallback(self):
        min_s, max_s = get_salary_range("unknown_category", 5)
        # Should fall back to "other"
        assert min_s > 0
        assert max_s > min_s

    def test_salary_increases_with_experience(self):
        junior_min, junior_max = get_salary_range("dev", 1)
        senior_min, senior_max = get_salary_range("dev", 12)
        assert senior_min > junior_min
        assert senior_max > junior_max


class TestGetSkillDemand:
    def test_known_skill_in_category(self):
        assert get_skill_demand("dev", "Python") == 9
        assert get_skill_demand("dev", "AI/ML") == 10

    def test_design_skill(self):
        assert get_skill_demand("design", "Figma") == 10

    def test_unknown_skill_returns_default(self):
        assert get_skill_demand("dev", "UnknownLanguage123") == 5

    def test_case_insensitive(self):
        assert get_skill_demand("dev", "python") == 9
        assert get_skill_demand("dev", "PYTHON") == 9

    def test_cross_category_match(self):
        # Python은 dev에 있지만 marketing에서 검색해도 찾아야 함
        result = get_skill_demand("marketing", "Python")
        assert result > 5  # dev 카테고리에서 매칭됨
