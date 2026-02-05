"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuthStore } from "@/stores/auth";
import { apiFetch } from "@/lib/api";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";

/* ── Types ───────────────────────────────────── */

interface Source {
  id: string;
  platform: string;
  source_url: string;
  status: string;
  parsed_data: Record<string, unknown> | null;
  last_scraped_at: string | null;
}

interface ScoreData {
  has_score: boolean;
  scores?: {
    expertise: number;
    influence: number;
    consistency: number;
    marketability: number;
    potential: number;
    total: number;
  };
  salary?: { min: number; max: number };
  analysis_accuracy?: number;
  insights?: {
    overall_summary?: string;
    strengths?: string[];
    weaknesses?: string[];
    expertise_detail?: string;
    influence_detail?: string;
    consistency_detail?: string;
    marketability_detail?: string;
    potential_detail?: string;
    market_position_percentile?: number;
  };
  scored_at?: string;
}

interface ActionItem {
  id: string;
  title: string;
  description: string | null;
  impact_percent: number | null;
  target_area: string | null;
  difficulty: string | null;
  estimated_duration: string | null;
  tags: string[];
  is_completed: boolean;
}

interface ActionsResponse {
  count: number;
  actions: ActionItem[];
}

/* ── Constants ───────────────────────────────── */

const AREAS = [
  { key: "expertise", label: "전문성", color: "#8B5CF6" },
  { key: "influence", label: "영향력", color: "#F59E0B" },
  { key: "consistency", label: "지속성", color: "#10B981" },
  { key: "marketability", label: "시장성", color: "#EF4444" },
  { key: "potential", label: "성장성", color: "#06B6D4" },
] as const;

const STATUS_LABELS: Record<string, string> = {
  pending: "대기 중",
  scraping: "수집 중",
  parsing: "분석 중",
  completed: "완료",
  failed: "실패",
};

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-gray-400",
  scraping: "bg-yellow-400",
  parsing: "bg-blue-400",
  completed: "bg-green-500",
  failed: "bg-red-500",
};

/* ── Component ───────────────────────────────── */

export default function DashboardPage() {
  const { accessToken } = useAuthStore();
  const [sources, setSources] = useState<Source[]>([]);
  const [scoreData, setScoreData] = useState<ScoreData | null>(null);
  const [topActions, setTopActions] = useState<ActionItem[]>([]);
  const [expandedArea, setExpandedArea] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!accessToken) return;

    Promise.all([
      apiFetch<Source[]>("/sources", { token: accessToken }).catch(() => []),
      apiFetch<ScoreData>("/scores/latest", { token: accessToken }).catch(
        () => null
      ),
      apiFetch<ActionsResponse>("/actions?sort=impact&completed=false", {
        token: accessToken,
      }).catch(() => null),
    ]).then(([sourcesRes, scoreRes, actionsRes]) => {
      setSources(sourcesRes);
      setScoreData(scoreRes);
      if (actionsRes) setTopActions(actionsRes.actions.slice(0, 3));
      setLoading(false);
    });
  }, [accessToken]);

  const scores = scoreData?.scores;
  const insights = scoreData?.insights;

  // Radar chart data
  const radarData = AREAS.map((a) => ({
    area: a.label,
    value: scores ? scores[a.key as keyof typeof scores] : 0,
    fullMark: 100,
  }));

  const formatSalary = (val: number) => {
    if (val >= 10000) return `${(val / 10000).toFixed(1)}억`;
    return `${val.toLocaleString()}만`;
  };

  const insightDetailKey = (key: string) =>
    `${key}_detail` as keyof NonNullable<typeof insights>;

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-[var(--color-primary)] border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="pt-4 pb-12">
      <h1 className="text-2xl font-bold">대시보드</h1>

      {/* ── No Score State ── */}
      {!scoreData?.has_score && (
        <div className="mt-8 flex flex-col items-center justify-center rounded-2xl border border-[var(--border)] bg-[var(--card)] p-12 text-center">
          <p className="text-lg font-medium">아직 분석 결과가 없습니다</p>
          <p className="mt-2 text-sm text-[var(--muted-foreground)]">
            온보딩에서 프로필을 등록하면 AI가 커리어를 분석해드려요.
          </p>
        </div>
      )}

      {/* ── Score Dashboard ── */}
      {scoreData?.has_score && scores && (
        <>
          {/* Total Score + Salary */}
          <div className="mt-6 flex flex-col gap-4 sm:flex-row">
            <div className="flex-1 rounded-2xl border border-[var(--border)] bg-[var(--card)] p-6 text-center">
              <p className="text-sm text-[var(--muted-foreground)]">종합 점수</p>
              <p className="mt-2 text-5xl font-bold text-[var(--color-primary)]">
                {scores.total}
              </p>
              <p className="mt-1 text-xs text-[var(--muted-foreground)]">/ 100</p>
              {insights?.market_position_percentile && (
                <p className="mt-2 text-sm font-medium text-[var(--color-primary)]">
                  상위 {100 - insights.market_position_percentile}%
                </p>
              )}
            </div>

            {scoreData.salary && (
              <div className="flex-1 rounded-2xl border border-[var(--border)] bg-[var(--card)] p-6 text-center">
                <p className="text-sm text-[var(--muted-foreground)]">예상 연봉 범위</p>
                <p className="mt-2 text-3xl font-bold">
                  {formatSalary(scoreData.salary.min)}
                  <span className="mx-2 text-lg text-[var(--muted-foreground)]">~</span>
                  {formatSalary(scoreData.salary.max)}
                </p>
                <p className="mt-1 text-xs text-[var(--muted-foreground)]">원 (연간)</p>
              </div>
            )}
          </div>

          {/* Radar Chart */}
          <div className="mt-6 rounded-2xl border border-[var(--border)] bg-[var(--card)] p-6">
            <h2 className="text-lg font-bold">5대 영역 분석</h2>
            <div className="mx-auto mt-4 h-72 w-full max-w-md">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid stroke="var(--border)" />
                  <PolarAngleAxis
                    dataKey="area"
                    tick={{ fill: "var(--foreground)", fontSize: 13 }}
                  />
                  <PolarRadiusAxis
                    angle={90}
                    domain={[0, 100]}
                    tick={{ fill: "var(--muted-foreground)", fontSize: 10 }}
                  />
                  <Radar
                    name="점수"
                    dataKey="value"
                    stroke="var(--color-primary)"
                    fill="var(--color-primary)"
                    fillOpacity={0.25}
                    strokeWidth={2}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Score Cards */}
          <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-5">
            {AREAS.map((area) => {
              const val = scores[area.key as keyof typeof scores];
              const isExpanded = expandedArea === area.key;
              return (
                <button
                  key={area.key}
                  onClick={() =>
                    setExpandedArea(isExpanded ? null : area.key)
                  }
                  className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4 text-center transition hover:border-[var(--color-primary)]"
                >
                  <p className="text-xs text-[var(--muted-foreground)]">
                    {area.label}
                  </p>
                  <p
                    className="mt-1 text-2xl font-bold"
                    style={{ color: area.color }}
                  >
                    {val}
                  </p>
                </button>
              );
            })}
          </div>

          {/* Area Detail */}
          {expandedArea && insights && (
            <div className="mt-4 rounded-xl border border-[var(--color-primary)] bg-[var(--card)] p-5">
              <h3 className="font-bold" style={{
                color: AREAS.find((a) => a.key === expandedArea)?.color,
              }}>
                {AREAS.find((a) => a.key === expandedArea)?.label} 상세 분석
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-[var(--foreground)]">
                {insights[insightDetailKey(expandedArea)] as string ||
                  "상세 분석 데이터가 없습니다."}
              </p>
            </div>
          )}

          {/* Overall Insights */}
          {insights?.overall_summary && (
            <div className="mt-6 rounded-2xl border border-[var(--border)] bg-[var(--card)] p-6">
              <h2 className="text-lg font-bold">AI 분석 인사이트</h2>
              <p className="mt-3 text-sm leading-relaxed">
                {insights.overall_summary}
              </p>

              {insights.strengths && insights.strengths.length > 0 && (
                <div className="mt-4">
                  <p className="text-sm font-medium text-green-600">강점</p>
                  <ul className="mt-1 space-y-1">
                    {insights.strengths.map((s, i) => (
                      <li key={i} className="text-sm text-[var(--foreground)]">
                        + {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {insights.weaknesses && insights.weaknesses.length > 0 && (
                <div className="mt-4">
                  <p className="text-sm font-medium text-red-500">개선 포인트</p>
                  <ul className="mt-1 space-y-1">
                    {insights.weaknesses.map((w, i) => (
                      <li key={i} className="text-sm text-[var(--foreground)]">
                        - {w}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {scoreData.analysis_accuracy && (
                <div className="mt-4 flex items-center gap-3">
                  <p className="text-xs text-[var(--muted-foreground)]">
                    분석 정확도
                  </p>
                  <div className="h-2 flex-1 rounded-full bg-[var(--muted)]">
                    <div
                      className="h-2 rounded-full bg-[var(--color-primary)] transition-all"
                      style={{ width: `${scoreData.analysis_accuracy}%` }}
                    />
                  </div>
                  <p className="text-xs font-medium">
                    {scoreData.analysis_accuracy}%
                  </p>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* ── Registered Sources ── */}
      <div className="mt-8">
        <h2 className="text-lg font-bold">등록된 프로필</h2>
        <div className="mt-3 space-y-3">
          {sources.length === 0 ? (
            <p className="text-sm text-[var(--muted-foreground)]">
              등록된 프로필이 없습니다.
            </p>
          ) : (
            sources.map((source) => (
              <div
                key={source.id}
                className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4"
              >
                <div className="flex items-center justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="rounded bg-[var(--color-primary)] px-2 py-0.5 text-xs font-medium text-white">
                        {source.platform}
                      </span>
                      <span className="flex items-center gap-1 text-xs">
                        <span
                          className={`inline-block h-2 w-2 rounded-full ${STATUS_COLORS[source.status] || "bg-gray-400"}`}
                        />
                        {STATUS_LABELS[source.status] || source.status}
                      </span>
                    </div>
                    <p className="mt-1 truncate text-sm text-[var(--muted-foreground)]">
                      {source.source_url}
                    </p>
                  </div>
                </div>

                {source.parsed_data && source.status === "completed" && (
                  <div className="mt-3 rounded-lg bg-[var(--muted)] p-3">
                    <p className="text-xs font-medium text-[var(--muted-foreground)]">
                      추출된 데이터
                    </p>
                    <div className="mt-1 space-y-1 text-sm">
                      {Boolean(source.parsed_data.name) && (
                        <p>
                          이름:{" "}
                          <strong>{String(source.parsed_data.name)}</strong>
                        </p>
                      )}
                      {Boolean(source.parsed_data.current_title) && (
                        <p>
                          직함: {String(source.parsed_data.current_title)}
                        </p>
                      )}
                      {Boolean(source.parsed_data.role_or_title) && (
                        <p>
                          역할: {String(source.parsed_data.role_or_title)}
                        </p>
                      )}
                      {Array.isArray(source.parsed_data.skills) && (
                        <p>
                          스킬:{" "}
                          {(source.parsed_data.skills as string[])
                            .slice(0, 5)
                            .join(", ")}
                        </p>
                      )}
                      {Boolean(source.parsed_data.data_quality) && (
                        <p className="text-xs text-[var(--muted-foreground)]">
                          데이터 품질:{" "}
                          {String(source.parsed_data.data_quality)}
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {source.status === "failed" && source.parsed_data === null && (
                  <p className="mt-2 text-xs text-red-500">
                    데이터 수집에 실패했습니다. 공개 프로필인지 확인해주세요.
                  </p>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* ── Top Actions ── */}
      <div className="mt-8">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold">추천 액션</h2>
          {topActions.length > 0 && (
            <Link
              href="/actions"
              className="text-sm font-medium text-[var(--color-primary)] hover:underline"
            >
              전체 보기
            </Link>
          )}
        </div>
        <div className="mt-3 space-y-3">
          {topActions.length === 0 ? (
            <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-5 text-center">
              <p className="text-sm text-[var(--muted-foreground)]">
                {scoreData?.has_score
                  ? "추천 액션을 생성 중입니다..."
                  : "프로필 분석이 완료되면 맞춤 액션이 추천됩니다."}
              </p>
            </div>
          ) : (
            topActions.map((action) => (
              <Link
                key={action.id}
                href="/actions"
                className="block rounded-xl border border-[var(--border)] bg-[var(--card)] p-4 transition hover:border-[var(--color-primary)]"
              >
                <div className="flex items-center gap-2">
                  {action.target_area && (
                    <span
                      className="rounded px-2 py-0.5 text-xs font-medium text-white"
                      style={{
                        backgroundColor:
                          AREAS.find((a) => a.key === action.target_area)
                            ?.color || "#6B7280",
                      }}
                    >
                      {AREAS.find((a) => a.key === action.target_area)
                        ?.label || action.target_area}
                    </span>
                  )}
                  {action.impact_percent && (
                    <span className="text-xs font-bold text-[var(--color-primary)]">
                      +{action.impact_percent}%
                    </span>
                  )}
                </div>
                <h3 className="mt-2 text-sm font-bold">{action.title}</h3>
                {action.description && (
                  <p className="mt-1 line-clamp-2 text-xs text-[var(--muted-foreground)]">
                    {action.description}
                  </p>
                )}
              </Link>
            ))
          )}
        </div>
      </div>

      {/* ── Nudge: Add More Data ── */}
      {scoreData?.has_score && scoreData.analysis_accuracy && scoreData.analysis_accuracy < 80 && (
        <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-4">
          <p className="text-sm font-medium text-amber-800">
            더 많은 프로필을 연동하면 분석 정확도가 높아집니다
          </p>
          <p className="mt-1 text-xs text-amber-600">
            현재 정확도 {scoreData.analysis_accuracy}% — 프로필을 추가하면
            최대 {Math.min(Math.round(scoreData.analysis_accuracy + 15), 100)}%까지 올릴 수 있어요.
          </p>
          <Link
            href="/onboarding"
            className="mt-3 inline-block rounded-lg bg-amber-600 px-4 py-2 text-xs font-medium text-white transition hover:bg-amber-700"
          >
            프로필 추가하기
          </Link>
        </div>
      )}
    </div>
  );
}
