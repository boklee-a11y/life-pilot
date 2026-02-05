# Life_Pilot MVP 상세 요구사항 정의서

> "데이터로 증명하고, 액션으로 성장하는 커리어 내비게이션"
>
> 작성일: 2026-02-05
> 버전: v1.0 (MVP)

---

## 1. 프로젝트 개요

| 항목 | 내용 |
|------|------|
| 서비스명 | Life_Pilot (라이프 파일럿) |
| 플랫폼 | 모바일 반응형 웹 (Mobile-First Responsive Web) |
| 프론트엔드 | Next.js 14+ (App Router, React 18+, TypeScript) |
| 백엔드 | Python FastAPI |
| AI 엔진 | Anthropic Claude API |
| MVP 범위 | Step 1~4 전체 (온보딩 → 진단 → 액션플랜 → 리텐션) |
| 타겟 유저 | 커리어 성장에 목마른 사회초년생 ~ 10년차 직장인 |
| 슬로건 | "데이터를 줄수록, 당신의 커리어 경로는 선명해집니다." |

---

## 2. 시스템 아키텍처

```
[Client Layer]
  Next.js (App Router, SSR/CSR)
  ├── 모바일 반응형 UI (Tailwind CSS)
  ├── 차트 시각화 (Recharts / Chart.js)
  └── 상태관리 (Zustand)

[API Gateway / BFF]
  Next.js API Routes (인증, 프록시)

[Backend Layer]
  FastAPI (Python)
  ├── Auth Service (Google OAuth2 + JWT)
  ├── URL Scraping Service (프로필 URL → 공개 데이터 수집)
  ├── AI Analysis Engine (Claude API 기반 통합 분석)
  ├── Action Recommendation Engine
  └── Notification Service

[Data Layer]
  PostgreSQL (메인 DB)
  Redis (캐싱, 세션)

[External Services]
  Claude API (Anthropic) -- 스크래핑 데이터 분석 + 스코어링 + 추천
  Google OAuth (로그인 전용)
```

---

## 3. 기능 요구사항 (Functional Requirements)

### FR-01. 사용자 인증 및 계정 관리

| ID | 요구사항 | 우선순위 | 상세 |
|----|---------|---------|------|
| FR-01-01 | 소셜 로그인 | P0 | Google OAuth 2.0 |
| FR-01-02 | 이메일 회원가입 | P1 | 이메일 + 비밀번호 기반 (이메일 인증) |
| FR-01-03 | JWT 기반 인증 | P0 | Access Token (15분) + Refresh Token (7일) |
| FR-01-04 | 프로필 관리 | P1 | 이름, 직군, 경력연차, 프로필 이미지 |
| FR-01-05 | 계정 탈퇴 | P1 | 데이터 완전 삭제 (GDPR 준수) |

### FR-02. 온보딩 (Step 1: Quick Start)

| ID | 요구사항 | 우선순위 | 상세 |
|----|---------|---------|------|
| FR-02-01 | 온보딩 진입 화면 | P0 | "30초 만에 분석하는 나의 시장 가치" 문구 + CTA 버튼 |
| FR-02-02 | 프로필 URL 입력 (최소 1개) | P0 | 어떤 플랫폼이든 자신의 프로필 URL을 최소 1개 이상 입력. 지원 플랫폼 목록 안내 + 자유 URL 입력 가능 |
| FR-02-03 | 추가 URL 입력 유도 | P1 | "프로필을 추가할수록 분석이 정교해집니다" 문구로 추가 URL / 이력서 PDF 업로드 유도 |
| FR-02-04 | 직군/분야 선택 | P0 | 개발, 디자인, PM, 마케팅, 데이터 등 직군 선택 (스코어링 기준값 결정용) |
| FR-02-05 | 온보딩 프로그레스 바 | P1 | 단계별 진행률 표시 (3~4단계) |
| FR-02-06 | 분석 로딩 화면 | P0 | 데이터 수집 → AI 분석 중 로딩 애니메이션 + 예상 소요 시간 표시 |

**온보딩 URL 입력 UI:**
- 플랫폼 아이콘 프리셋 버튼 (LinkedIn, GitHub, Velog, Tistory, Dribbble 등) + "기타 URL" 버튼
- 프리셋 클릭 시 해당 플랫폼 URL 입력 필드 활성화
- "기타 URL" 클릭 시 자유 URL 입력 + 플랫폼명 직접 기재
- 최소 1개 URL 입력 시 "분석 시작" 버튼 활성화
- 이력서 PDF 업로드도 1개 소스로 인정

### FR-03. 프로필 URL 기반 데이터 수집

> **핵심 방식:** 유저가 어떤 플랫폼이든 자신의 프로필 URL을 입력하면, 백엔드가 해당 페이지의 공개 데이터를 스크래핑한 뒤 Claude API로 구조화된 정보를 추출한다. 특정 플랫폼에 종속되지 않는 범용 구조.

| ID | 요구사항 | 우선순위 | 상세 |
|----|---------|---------|------|
| FR-03-01 | 범용 URL 스크래핑 | P0 | 어떤 URL이든 입력 → 공개 페이지 스크래핑 → Claude API가 플랫폼 특성에 맞게 구조화 |
| FR-03-02 | 플랫폼 자동 감지 | P0 | URL 도메인 기반으로 알려진 플랫폼 자동 감지 (LinkedIn, GitHub, Velog 등). 미감지 시 "기타"로 분류 |
| FR-03-03 | 기타/커스텀 URL 지원 | P0 | 개인 블로그, 포트폴리오 사이트, Notion, Behance 등 미리 정의되지 않은 URL도 스크래핑 + AI 분석 가능 |
| FR-03-04 | 이력서 PDF 파싱 | P1 | PDF 업로드 → Claude API로 텍스트 추출 및 구조화 |
| FR-03-05 | URL 유효성 검증 | P0 | 입력된 URL 형식 검증 + 접근 가능 여부 확인 + 공개 페이지 여부 체크 |
| FR-03-06 | 데이터 재수집 | P1 | 수동 "다시 분석하기" 버튼 → URL 재스크래핑 → 점수 재산출 |

**URL → 분석 파이프라인:**
```
1. 유저가 프로필 URL 입력 (예: github.com/username, velog.io/@username 등)
2. URL 유효성 검증 + 도메인 기반 플랫폼 자동 감지 (알려진 플랫폼 or "기타")
3. 백엔드에서 공개 페이지 스크래핑 (Playwright/httpx + BeautifulSoup)
4. 스크래핑된 HTML/텍스트를 Claude API에 전달
   - 알려진 플랫폼: 해당 플랫폼에 최적화된 프롬프트로 구조화
   - 기타 URL: 범용 프롬프트로 커리어 관련 정보 추출
5. Claude가 구조화된 JSON 데이터로 변환:
   {
     "platform": "github",       // 또는 "velog", "personal_blog", "other" 등
     "profile_url": "https://github.com/username",
     "extracted_data": {
       "name": "홍길동",
       "role_or_title": "Backend Engineer",
       "skills": ["Python", "AWS", "Kubernetes"],
       "projects": [...],
       "activity_summary": "주 3회 이상 커밋, 12개 공개 Repo 운영",
       "quantitative_metrics": {
         "followers": 150,
         "total_stars": 340,
         "post_count": null
       }
     },
     "data_quality": "high"      // high/medium/low - 추출 신뢰도
   }
6. 구조화된 데이터를 DB에 저장 → 스코어링 엔진으로 전달
```

**알려진 플랫폼 (프리셋) - 최적화된 스크래핑:**

| 플랫폼 | URL 패턴 | 수집 대상 (공개 데이터) |
|--------|----------|----------------------|
| LinkedIn | `linkedin.com/in/*` | 직함, 경력, 스킬, 학력, 자격증, 추천 수, 활동 요약 |
| GitHub | `github.com/*` | 프로필 요약, Pinned Repo, 기여 그래프, 언어 비율, 팔로워/팔로잉 |
| Velog | `velog.io/@*` | 글 목록, 태그, 게시 빈도, 시리즈 |
| Tistory | `*.tistory.com` | 글 목록, 카테고리, 최근 활동 |
| Dribbble | `dribbble.com/*` | 작업물 수, 좋아요, 팔로워 |
| Behance | `behance.net/*` | 프로젝트 수, 감사, 팔로워 |
| Notion | `notion.so/*` | 포트폴리오/이력서 페이지 내용 |

**기타 URL (커스텀) - 범용 AI 분석:**

| 유형 | 예시 | AI 추출 방식 |
|------|------|-------------|
| 개인 블로그 | `myblog.dev` | 글 목록, 기술 주제, 활동 빈도 자동 추출 |
| 포트폴리오 사이트 | `myportfolio.com` | 프로젝트 목록, 사용 기술, 경력 정보 추출 |
| 기타 프로필 | `medium.com/@user` 등 | Claude API가 페이지 맥락에 맞게 커리어 관련 정보 추출 |

### FR-04. 커리어 진단 - 5대 영역 스코어링 (Step 2)

| ID | 요구사항 | 우선순위 | 상세 |
|----|---------|---------|------|
| FR-04-01 | 전문성 (Expertise) 스코어 | P0 | 0~100점. 보유 기술 수 & 희소성, 프로젝트 난이도, 경력 연차, 자격증 |
| FR-04-02 | 영향력 (Influence) 스코어 | P0 | 0~100점. SNS 팔로워, 블로그 방문자/구독자, 오픈소스 기여(Star, Fork), 추천서 수 |
| FR-04-03 | 지속성 (Consistency) 스코어 | P0 | 0~100점. 활동 빈도(GitHub 커밋, 블로그 포스팅), 학습 로그 연속성, 근속 연수 |
| FR-04-04 | 시장성 (Marketability) 스코어 | P0 | 0~100점. 현재 시장 내 직군/스택 수요 (사전 정의된 시장 데이터 테이블 기반) |
| FR-04-05 | 성장성 (Potential) 스코어 | P0 | 0~100점. 최신 기술 습득 비율, 교육/자격증 이수 속도, 최근 6개월 활동 추세 |
| FR-04-06 | Radar Chart 시각화 | P0 | 5각형 레이더 차트로 5대 영역 점수 시각화 |
| FR-04-07 | 영역별 상세 리포트 | P1 | 각 영역 클릭 시 상세 분석 근거 및 개선 포인트 표시 |
| FR-04-08 | 동일 직군 대비 포지셔닝 | P1 | 같은 직군/연차 대비 상대적 위치 (상위 N%) 표시 |

**스코어링 로직 (Claude API + 규칙 기반 하이브리드):**

```
1단계: 규칙 기반 정량 점수 산출
  - 각 영역별 수집 데이터를 가중치 공식에 대입
  - 예: Expertise = (기술수 × 희소성가중치 × 0.3) + (프로젝트수 × 난이도 × 0.3)
                    + (경력연차 × 0.2) + (자격증 × 0.2)

2단계: Claude API 정성 분석 보정
  - 수집된 텍스트 데이터(경력 설명, 프로젝트 설명 등)를 Claude에 전달
  - 정량 점수 대비 보정값 (-10 ~ +10) 산출
  - 영역별 강점/약점 인사이트 자연어 생성
```

### FR-05. 시장 가치 측정

| ID | 요구사항 | 우선순위 | 상세 |
|----|---------|---------|------|
| FR-05-01 | 예상 연봉 범위 산출 | P0 | 5대 영역 종합 스코어 + 직군/연차 기반 연봉 범위 (하한~상한) 표시 |
| FR-05-02 | 연봉 데이터 기반 | P1 | 사전 수집된 직군별/연차별 연봉 테이블 (초기에는 공개 데이터 기반 정적 테이블) |
| FR-05-03 | 시장 가치 변화 추이 | P2 | 시간에 따른 예상 연봉 변화 그래프 (분석 이력 기반) |

### FR-06. 성장 액션 플랜 (Step 3: Actionable Insights)

| ID | 요구사항 | 우선순위 | 상세 |
|----|---------|---------|------|
| FR-06-01 | 개인화 액션 추천 | P0 | Claude API 기반. 약점 보완 + 강점 극대화 전략 2트랙 추천 |
| FR-06-02 | 카드 형태 UI | P0 | 각 추천 액션을 카드로 표시: 제목, 설명, 예상 가치 상승 효과 (%), 태그, CTA 버튼 |
| FR-06-03 | 태그 시스템 | P1 | #스킬업 #네트워킹 #글쓰기 #멘토링 #채용 등 필터링 가능한 태그 |
| FR-06-04 | CTA 연결 | P1 | [강의 신청하기] → 외부 링크, [블로그 초안 생성] → Claude로 초안 생성, [커피챗 요청하기] → 추후 연동 |
| FR-06-05 | 액션 우선순위 정렬 | P1 | 가치 상승 효과 순 / 난이도 순 / 소요 시간 순 정렬 |
| FR-06-06 | 액션 북마크 | P2 | 관심 있는 액션 저장 기능 |

**Claude API 프롬프트 설계 (액션 추천):**

```json
// Input: 5대 영역 스코어, 직군, 경력, 보유 스킬, 현재 활동 데이터
// Output (JSON):
{
  "actions": [
    {
      "title": "AWS Solutions Architect 자격증 취득",
      "description": "클라우드 역량 증명으로 시장 가치 즉시 상승",
      "impact_percent": 8,
      "target_area": "expertise",
      "difficulty": "medium",
      "estimated_duration": "2개월",
      "tags": ["스킬업", "자격증"],
      "cta": { "label": "학습 로드맵 보기", "url": "..." }
    }
  ]
}
```

### FR-07. 리텐션 루프 (Step 4)

| ID | 요구사항 | 우선순위 | 상세 |
|----|---------|---------|------|
| FR-07-01 | 액션 완료 체크 | P0 | 추천 액션의 완료 상태 토글 (완료/미완료) |
| FR-07-02 | 데이터 재스크래핑 | P0 | 액션 완료 시 등록된 URL 재스크래핑 → 점수 즉시 업데이트 |
| FR-07-03 | 점수 변화 히스토리 | P1 | 이전 스코어 대비 변화량 표시 (예: Expertise +5) |
| FR-07-04 | 정보 추가 유도 | P1 | "이 정보를 추가하면 분석 정확도가 25% 상승합니다" 등 넛지 메시지 |
| FR-07-05 | 이메일 알림 | P2 | 주간 리포트 이메일 (점수 변화, 새 추천 액션) |

### FR-08. 대시보드 (메인 화면)

| ID | 요구사항 | 우선순위 | 상세 |
|----|---------|---------|------|
| FR-08-01 | 종합 대시보드 | P0 | Radar Chart + 종합 스코어 + 예상 연봉 범위 한눈에 표시 |
| FR-08-02 | 등록 URL 현황 | P1 | 등록된 프로필 URL 목록 + 마지막 스크래핑 시간 |
| FR-08-03 | 추천 액션 요약 | P0 | 상위 3개 추천 액션 카드 표시 |
| FR-08-04 | 공유 기능 | P1 | 결과 페이지 이미지/링크 공유 (SNS, 카카오톡 등) |
| FR-08-05 | 분석 정확도 표시 | P2 | 연동 데이터 기반 분석 정확도 게이지 (데이터 추가 유도) |

---

## 4. 비기능 요구사항 (Non-Functional Requirements)

| ID | 항목 | 요구사항 |
|----|------|---------|
| NFR-01 | 성능 | 페이지 로딩 3초 이내 (LCP), 첫 분석 결과 30초 이내 |
| NFR-02 | 반응형 | Mobile-First. 최소 지원: 360px ~ 1440px |
| NFR-03 | 브라우저 호환 | Chrome, Safari, Edge 최신 2개 버전 |
| NFR-04 | 가용성 | 99.5% 이상 (월간) |
| NFR-05 | 보안 | HTTPS 전용, 민감 데이터 암호화 (AES-256), OWASP Top 10 대응 |
| NFR-06 | 확장성 | 초기 동시 사용자 1,000명 처리 가능 |
| NFR-07 | 접근성 | WCAG 2.1 AA 수준 기본 대응 |
| NFR-08 | 국제화 | MVP는 한국어 단일 언어, 다국어 확장 가능 구조 |

---

## 5. 데이터 모델 (ERD 주요 테이블)

```sql
-- 사용자 테이블
CREATE TABLE users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email         VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255),          -- 이메일 가입 시
  name          VARCHAR(100) NOT NULL,
  profile_image_url TEXT,
  job_category  VARCHAR(50),           -- 직군 (dev/design/pm/marketing/data)
  years_of_experience INTEGER,         -- 경력 연차
  auth_provider VARCHAR(20) NOT NULL,  -- google/email
  created_at    TIMESTAMP DEFAULT NOW(),
  updated_at    TIMESTAMP DEFAULT NOW()
);

-- 프로필 URL 데이터 소스 테이블
CREATE TABLE data_sources (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
  platform        VARCHAR(30) NOT NULL,  -- linkedin/github/velog/tistory/dribbble/behance/notion/resume/other
  source_url      TEXT NOT NULL,          -- 유저가 입력한 프로필 URL
  scraped_html    TEXT,                   -- 스크래핑된 원본 HTML/텍스트
  parsed_data     JSONB,                  -- Claude API가 구조화한 데이터
  is_confirmed    BOOLEAN DEFAULT FALSE,  -- 유저가 스크래핑 결과를 확인했는지
  last_scraped_at TIMESTAMP,
  status          VARCHAR(20) DEFAULT 'pending', -- pending/scraping/parsing/completed/failed
  error_message   TEXT,                   -- 실패 시 에러 메시지
  created_at      TIMESTAMP DEFAULT NOW()
);

-- 커리어 스코어 테이블
CREATE TABLE career_scores (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             UUID REFERENCES users(id) ON DELETE CASCADE,
  expertise_score     DECIMAL(5,2),    -- 전문성 (0-100)
  influence_score     DECIMAL(5,2),    -- 영향력 (0-100)
  consistency_score   DECIMAL(5,2),    -- 지속성 (0-100)
  marketability_score DECIMAL(5,2),    -- 시장성 (0-100)
  potential_score     DECIMAL(5,2),    -- 성장성 (0-100)
  total_score         DECIMAL(5,2),    -- 종합 (0-100)
  estimated_salary_min BIGINT,         -- 예상 연봉 하한
  estimated_salary_max BIGINT,         -- 예상 연봉 상한
  analysis_accuracy   DECIMAL(5,2),    -- 분석 정확도 (%)
  ai_insights         JSONB,           -- Claude 분석 결과
  scored_at           TIMESTAMP DEFAULT NOW(),
  created_at          TIMESTAMP DEFAULT NOW()
);

-- 액션 추천 테이블
CREATE TABLE action_recommendations (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID REFERENCES users(id) ON DELETE CASCADE,
  score_id          UUID REFERENCES career_scores(id),
  title             VARCHAR(200) NOT NULL,
  description       TEXT,
  impact_percent    DECIMAL(5,2),      -- 예상 가치 상승률
  target_area       VARCHAR(20),       -- expertise/influence/consistency/marketability/potential
  difficulty        VARCHAR(10),       -- easy/medium/hard
  estimated_duration VARCHAR(50),      -- 예상 소요 시간
  tags              TEXT[],            -- 태그 배열
  cta_label         VARCHAR(100),
  cta_url           TEXT,
  is_completed      BOOLEAN DEFAULT FALSE,
  completed_at      TIMESTAMP,
  is_bookmarked     BOOLEAN DEFAULT FALSE,
  created_at        TIMESTAMP DEFAULT NOW()
);

-- 스코어 변화 히스토리 테이블
CREATE TABLE score_history (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
  score_id    UUID REFERENCES career_scores(id),
  snapshot    JSONB NOT NULL,          -- 시점별 전체 스코어 스냅샷
  created_at  TIMESTAMP DEFAULT NOW()
);

-- 시장 데이터 테이블 (초기 정적 데이터)
CREATE TABLE market_data (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_category    VARCHAR(50) NOT NULL,
  skill_name      VARCHAR(100),
  demand_level    INTEGER CHECK (demand_level BETWEEN 1 AND 10),
  avg_salary_min  BIGINT,
  avg_salary_max  BIGINT,
  years_range     VARCHAR(20),         -- 연차 구간 (예: "1-3", "4-7", "8-10")
  updated_at      TIMESTAMP DEFAULT NOW()
);
```

---

## 6. API 설계 (주요 엔드포인트)

### 6.1 인증 (Auth)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/auth/signup` | 이메일 회원가입 |
| POST | `/api/v1/auth/login` | 로그인 (JWT 발급) |
| POST | `/api/v1/auth/oauth/google` | Google OAuth 콜백 |
| POST | `/api/v1/auth/refresh` | 토큰 갱신 |
| DELETE | `/api/v1/auth/account` | 계정 탈퇴 |

### 6.2 온보딩 & 프로필 URL 등록
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/onboarding/profile` | 직군/연차 등 기본 정보 저장 |
| POST | `/api/v1/sources` | 프로필 URL 등록 (URL + 플랫폼 자동 감지) |
| GET | `/api/v1/sources` | 등록된 프로필 URL 목록 조회 |
| POST | `/api/v1/sources/{id}/rescan` | 특정 URL 재스크래핑 요청 |
| DELETE | `/api/v1/sources/{id}` | 프로필 URL 삭제 |
| POST | `/api/v1/sources/resume/upload` | 이력서 PDF 업로드 |
| GET | `/api/v1/sources/{id}/preview` | 스크래핑 결과 미리보기 (유저 확인용) |
| PATCH | `/api/v1/sources/{id}/confirm` | 스크래핑 결과 확인/수정 후 확정 |

### 6.3 커리어 분석
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/analysis/run` | 분석 실행 (비동기, Job ID 반환) |
| GET | `/api/v1/analysis/status/{jobId}` | 분석 진행 상태 조회 |
| GET | `/api/v1/scores/latest` | 최신 스코어 조회 |
| GET | `/api/v1/scores/history` | 스코어 변화 히스토리 |
| GET | `/api/v1/scores/{id}/detail` | 영역별 상세 분석 결과 |
| GET | `/api/v1/market-position` | 동일 직군 대비 포지셔닝 |

### 6.4 액션 추천
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/actions` | 추천 액션 목록 (필터: tag, area, sort) |
| PATCH | `/api/v1/actions/{id}/complete` | 액션 완료 체크 |
| PATCH | `/api/v1/actions/{id}/bookmark` | 액션 북마크 토글 |
| POST | `/api/v1/actions/generate-draft` | 블로그 초안 생성 (Claude API) |

### 6.5 공유
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/share/generate` | 공유용 이미지/링크 생성 |
| GET | `/api/v1/share/{shareId}` | 공유 결과 페이지 (Public) |

---

## 7. 프로필 URL 스크래핑 + AI 분석 상세

> OAuth 직접 연동 없이, **프로필 URL 입력 → 공개 페이지 스크래핑 → Claude API 분석**으로 동작한다.

### 7.1 전체 처리 흐름
```
[유저] URL 입력
  ↓
[FastAPI] URL 유효성 검증 + 플랫폼 감지
  ↓
[Scraper] 공개 페이지 스크래핑 (Playwright headless browser)
  ↓
[FastAPI] 스크래핑된 HTML/텍스트 정제
  ↓
[Claude API] 구조화된 데이터 추출 (JSON)
  ↓
[FastAPI] DB 저장 → 스코어링 엔진 호출
```

### 7.2 스크래핑 전략

> 알려진 플랫폼은 최적화된 스크래핑을, 기타 URL은 범용 스크래핑 + Claude AI 분석으로 처리한다. 특정 플랫폼이 필수가 아니므로, 어떤 URL 조합이든 분석 가능해야 한다.

**알려진 플랫폼 (프리셋):**

| 플랫폼 | 스크래핑 방식 | 수집 데이터 | 제한/주의사항 |
|--------|-------------|------------|-------------|
| LinkedIn | Playwright (동적 렌더링 필요) | 직함, 경력, 스킬, 학력, 자격증, 추천 수 | 공개 프로필만. 비공개 시 안내 |
| GitHub | httpx + BeautifulSoup (정적 HTML) | 프로필 요약, Pinned Repo, 기여 그래프, 언어 비율 | Rate limit 주의 (IP당) |
| Velog | httpx + BeautifulSoup | 글 목록, 태그, 게시 빈도, 시리즈 | CSR 부분은 Playwright 대체 |
| Tistory | httpx + BeautifulSoup | 글 목록, 카테고리, 최근 활동 | 스킨별 HTML 구조 상이 가능 |
| Dribbble | httpx + BeautifulSoup | 작업물 수, 좋아요, 팔로워 | 공개 프로필만 |
| Behance | httpx + BeautifulSoup | 프로젝트 수, 감사, 팔로워 | 공개 프로필만 |
| 이력서 PDF | pdfplumber로 텍스트 추출 | 경력, 스킬, 프로젝트, 학력 | 최대 10MB, PDF만 지원 |

**기타/커스텀 URL (범용):**

| 유형 | 스크래핑 방식 | AI 분석 방식 |
|------|-------------|-------------|
| 개인 블로그 | Playwright (범용) | Claude가 페이지 콘텐츠에서 글 목록, 기술 주제, 활동 빈도 추출 |
| 포트폴리오 사이트 | Playwright (범용) | Claude가 프로젝트 목록, 사용 기술, 경력 정보 추출 |
| Notion 공개 페이지 | Playwright (범용) | Claude가 이력서/포트폴리오 구조 자동 인식 후 추출 |
| Medium, DEV.to 등 | httpx + BeautifulSoup | Claude가 글 목록, 주제, 반응 수 추출 |
| 기타 모든 URL | Playwright (범용) | Claude가 커리어 관련 정보를 최대한 추출 + data_quality 평가 |

### 7.3 Claude API 활용 포인트

| 용도 | 설명 | 호출 시점 |
|------|------|----------|
| 데이터 구조화 | 스크래핑된 비정형 텍스트 → 구조화된 JSON 변환 | URL 등록/재스캔 시 |
| 스코어링 보정 | 정량 점수에 대한 정성 분석 보정 (-10~+10) | 분석 실행 시 |
| 인사이트 생성 | 영역별 강점/약점 자연어 리포트 | 분석 실행 시 |
| 액션 추천 | 개인화된 성장 액션 플랜 생성 | 분석 완료 후 |
| 블로그 초안 | 추천 액션 중 "블로그 쓰기" CTA 실행 시 | 유저 요청 시 |

### 7.4 스크래핑 기술 스택
```
- Playwright (Python): 동적 페이지 렌더링 (SPA, 기타 커스텀 URL 범용 처리)
- httpx: 정적 페이지 HTTP 요청 (알려진 정적 사이트 우선 시도)
- BeautifulSoup4: HTML 파싱 및 데이터 추출
- pdfplumber: PDF 텍스트 추출
- Claude API (Anthropic SDK): 비정형 데이터 → 구조화 JSON 변환
```

### 7.5 제한사항 및 대응
| 제한사항 | 대응 방안 |
|---------|----------|
| 비공개 프로필 | "공개 프로필만 분석 가능합니다" 안내 + 이력서 PDF 업로드 유도 |
| 스크래핑 차단 (IP 밴, CAPTCHA) | 요청 간격 조절, User-Agent 로테이션, 실패 시 재시도 + 유저 안내 |
| HTML 구조 변경 | Claude API가 비정형 텍스트도 분석 가능하므로 CSS Selector 의존도 최소화 |
| 데이터 정확도 | 스크래핑 결과를 유저에게 확인/수정할 수 있는 "데이터 검토" 단계 제공 |

---

## 8. UI/UX 요구사항

### 8.1 주요 화면 목록

| 화면 | 경로 | 설명 |
|------|------|------|
| 랜딩 페이지 | `/` | 서비스 소개 + CTA "시작하기" |
| 로그인/회원가입 | `/auth` | 소셜 로그인 + 이메일 가입 |
| 온보딩 | `/onboarding` | 프로필 URL 입력 (최소 1개) → 직군 선택 → 분석 시작 |
| 분석 로딩 | `/analyzing` | AI 분석 중 로딩 화면 |
| 대시보드 (메인) | `/dashboard` | Radar Chart + 스코어 + 연봉 + 추천 액션 요약 |
| 영역별 상세 | `/dashboard/[area]` | 특정 영역 클릭 시 상세 분석 |
| 액션 플랜 | `/actions` | 전체 추천 액션 리스트 + 필터 |
| 데이터 소스 관리 | `/settings/sources` | 등록된 프로필 URL 현황 + 추가/삭제/재스캔 |
| 프로필 설정 | `/settings/profile` | 개인정보 + 계정 관리 |
| 공유 결과 페이지 | `/share/[id]` | 외부 공유용 (비로그인 접근 가능) |

### 8.2 디자인 원칙
- **Mobile-First**: 360px 기준 설계 후 데스크톱 확장
- **다크 모드**: 기본 라이트, 다크 모드 지원 (시스템 설정 연동)
- **컬러 시스템**: Primary Blue (#2563EB 계열) + 5대 영역별 고유 색상
- **타이포그래피**: Pretendard (한글), Inter (영문)
- **차트**: Radar Chart (5대 영역), Line Chart (추이), Gauge (연봉/정확도)
- **카드 UI**: 액션 추천은 스와이프 가능한 카드 리스트

---

## 9. 보안 요구사항

| 항목 | 상세 |
|------|------|
| 인증 | JWT (Access + Refresh), HttpOnly Secure Cookie |
| 비밀번호 | bcrypt (cost factor 12) |
| API 보안 | Rate Limiting (100 req/min/user), CORS 설정 |
| 데이터 암호화 | 전송: TLS 1.3, 저장: AES-256 (민감 데이터) |
| 스크래핑 데이터 | 수집된 개인 데이터 암호화 저장, 유저 삭제 요청 시 즉시 삭제 |
| XSS/CSRF | Next.js 기본 보호 + CSP 헤더 + CSRF 토큰 |
| 개인정보 | 수집 동의 절차, 탈퇴 시 30일 내 완전 삭제 |
| 환경변수 | .env 파일 분리, 시크릿 관리 (Docker Secrets / Cloud KMS) |

---

## 10. 인프라 및 배포

| 항목 | 기술 |
|------|------|
| 프론트엔드 배포 | Vercel (Next.js 최적화) |
| 백엔드 배포 | AWS EC2 또는 Railway / Render (초기) |
| 데이터베이스 | Supabase PostgreSQL 또는 AWS RDS |
| 캐싱 | Upstash Redis (서버리스) |
| 파일 저장 | AWS S3 (이력서 PDF) |
| CI/CD | GitHub Actions (lint → test → build → deploy) |
| 모니터링 | Sentry (에러), Vercel Analytics (프론트) |

---

## 11. MVP 개발 단계 (Phased Delivery)

### Phase 1: 기반 구축 (Foundation)
- [ ] 프로젝트 초기 세팅 (Next.js + FastAPI 모노레포)
- [ ] DB 스키마 설계 및 마이그레이션
- [ ] 사용자 인증 (Google OAuth + 이메일 + JWT)
- [ ] 기본 UI 레이아웃 + 모바일 반응형

### Phase 2: 온보딩 + URL 스크래핑
- [ ] 범용 URL 입력 → 스크래핑 파이프라인 구축 (Playwright + httpx + BeautifulSoup)
- [ ] 플랫폼 자동 감지 로직 (도메인 기반 프리셋 매칭 + 기타 URL 처리)
- [ ] Claude API 연동 (스크래핑 데이터 → 구조화 JSON 변환)
- [ ] 알려진 플랫폼 스크래핑 구현 (LinkedIn, GitHub 우선)
- [ ] 기타/커스텀 URL 범용 스크래핑 + AI 분석 구현
- [ ] 스크래핑 결과 미리보기 + 유저 확인 화면
- [ ] 온보딩 플로우 UI (플랫폼 프리셋 버튼 + 자유 URL 입력)
- [ ] 분석 로딩 화면

### Phase 3: 커리어 진단 엔진
- [ ] 5대 영역 규칙 기반 스코어링 로직
- [ ] Claude API 연동 (정성 분석 보정)
- [ ] 시장 데이터 테이블 구축
- [ ] Radar Chart + 대시보드 UI
- [ ] 예상 연봉 범위 산출

### Phase 4: 액션 플랜 + 리텐션
- [ ] Claude API 기반 액션 추천 엔진
- [ ] 액션 카드 UI + 필터/정렬
- [ ] 액션 완료 → 재스캔 → 점수 업데이트 루프
- [ ] 공유 기능
- [ ] 정보 추가 유도 넛지

---

## 12. 핵심 지표 추적 (Analytics)

| 지표 | 목표 | 추적 방법 |
|------|------|----------|
| 퍼널 전환율 | 80% 이상 | 가입 → 첫 결과 도달 (Mixpanel/Amplitude) |
| 프로필 URL 등록 수 | 평균 2개+ | 유저당 data_sources 테이블 count |
| WAU (주간 재방문) | 40% 이상 | 주간 활성 유저 / 전체 가입 유저 |
| 추천 액션 CTR | 25% 이상 | CTA 클릭 이벤트 / 노출 이벤트 |
| 바이럴 지수 | 10% 이상 | 공유 버튼 클릭 / 결과 페이지 조회 |

---

## 13. 검증 계획 (Verification)

### 단위 테스트
- 스코어링 로직 (각 영역별 점수 계산 정확성)
- API 엔드포인트 (FastAPI TestClient)
- 컴포넌트 렌더링 (React Testing Library)

### 통합 테스트
- 온보딩 → URL 입력 → 분석 → 결과 표시 전체 플로우
- URL 스크래핑 → Claude API 구조화 → DB 저장 파이프라인
- 비공개 프로필 / 잘못된 URL 등 에러 케이스 처리

### E2E 테스트
- Playwright: 주요 사용자 시나리오 자동화
- 모바일 뷰포트에서의 전체 플로우

### 수동 검증
- 실제 LinkedIn/GitHub 공개 프로필 URL로 스크래핑 + 분석 테스트
- 비공개 프로필, 존재하지 않는 URL 등 엣지 케이스 테스트
- 다양한 직군/연차 시나리오 테스트
- 모바일 기기 실기 테스트 (iOS Safari, Android Chrome)
