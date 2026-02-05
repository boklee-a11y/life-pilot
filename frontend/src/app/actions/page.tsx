"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/auth";
import { apiFetch } from "@/lib/api";

/* ── Types ───────────────────────────────────── */

interface Action {
  id: string;
  title: string;
  description: string | null;
  impact_percent: number | null;
  target_area: string | null;
  difficulty: string | null;
  estimated_duration: string | null;
  tags: string[];
  cta_label: string | null;
  cta_url: string | null;
  is_completed: boolean;
  completed_at: string | null;
  is_bookmarked: boolean;
}

interface ActionsResponse {
  count: number;
  actions: Action[];
}

/* ── Constants ───────────────────────────────── */

const AREA_LABELS: Record<string, string> = {
  expertise: "전문성",
  influence: "영향력",
  consistency: "지속성",
  marketability: "시장성",
  potential: "성장성",
};

const AREA_COLORS: Record<string, string> = {
  expertise: "#8B5CF6",
  influence: "#F59E0B",
  consistency: "#10B981",
  marketability: "#EF4444",
  potential: "#06B6D4",
};

const DIFFICULTY_LABELS: Record<string, string> = {
  easy: "쉬움",
  medium: "보통",
  hard: "어려움",
};

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: "bg-green-100 text-green-700",
  medium: "bg-yellow-100 text-yellow-700",
  hard: "bg-red-100 text-red-700",
};

const SORT_OPTIONS = [
  { value: "impact", label: "효과순" },
  { value: "difficulty", label: "난이도순" },
  { value: "recent", label: "최신순" },
];

/* ── Component ───────────────────────────────── */

export default function ActionsPage() {
  const { accessToken } = useAuthStore();
  const [actions, setActions] = useState<Action[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterArea, setFilterArea] = useState<string>("");
  const [filterTag, setFilterTag] = useState<string>("");
  const [sort, setSort] = useState("impact");
  const [showCompleted, setShowCompleted] = useState(false);

  const fetchActions = async () => {
    if (!accessToken) return;
    try {
      const params = new URLSearchParams();
      if (filterArea) params.set("area", filterArea);
      if (filterTag) params.set("tag", filterTag);
      params.set("sort", sort);

      const data = await apiFetch<ActionsResponse>(
        `/actions?${params.toString()}`,
        { token: accessToken }
      );
      setActions(data.actions);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActions();
  }, [accessToken, filterArea, filterTag, sort]);

  const handleComplete = async (actionId: string) => {
    if (!accessToken) return;
    try {
      await apiFetch(`/actions/${actionId}/complete`, {
        method: "PATCH",
        token: accessToken,
      });
      fetchActions();
    } catch {
      // ignore
    }
  };

  const handleBookmark = async (actionId: string) => {
    if (!accessToken) return;
    try {
      await apiFetch(`/actions/${actionId}/bookmark`, {
        method: "PATCH",
        token: accessToken,
      });
      fetchActions();
    } catch {
      // ignore
    }
  };

  // 모든 태그 수집
  const allTags = Array.from(new Set(actions.flatMap((a) => a.tags)));

  const filteredActions = actions.filter((a) => {
    if (!showCompleted && a.is_completed) return false;
    return true;
  });

  const pendingCount = actions.filter((a) => !a.is_completed).length;
  const completedCount = actions.filter((a) => a.is_completed).length;

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-[var(--color-primary)] border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="pt-4 pb-12">
      <h1 className="text-2xl font-bold">성장 액션 플랜</h1>
      <p className="mt-2 text-[var(--muted-foreground)]">
        AI가 추천한 맞춤 액션으로 커리어를 성장시키세요.
      </p>

      {/* Stats */}
      {actions.length > 0 && (
        <div className="mt-4 flex gap-4">
          <div className="flex items-center gap-2 rounded-lg bg-[var(--color-primary)] px-3 py-1.5 text-sm font-medium text-white">
            {pendingCount}개 진행 중
          </div>
          <button
            onClick={() => setShowCompleted(!showCompleted)}
            className={`rounded-lg border px-3 py-1.5 text-sm transition ${
              showCompleted
                ? "border-green-500 bg-green-50 text-green-700"
                : "border-[var(--border)]"
            }`}
          >
            {completedCount}개 완료 {showCompleted ? "(숨기기)" : "(보기)"}
          </button>
        </div>
      )}

      {/* Filters */}
      {actions.length > 0 && (
        <div className="mt-4 space-y-3">
          {/* Area Filter */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setFilterArea("")}
              className={`rounded-lg border px-3 py-1.5 text-xs transition ${
                !filterArea
                  ? "border-[var(--color-primary)] bg-[var(--color-primary)] text-white"
                  : "border-[var(--border)] hover:border-[var(--color-primary)]"
              }`}
            >
              전체
            </button>
            {Object.entries(AREA_LABELS).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setFilterArea(filterArea === key ? "" : key)}
                className={`rounded-lg border px-3 py-1.5 text-xs transition ${
                  filterArea === key
                    ? "border-[var(--color-primary)] text-white"
                    : "border-[var(--border)] hover:border-[var(--color-primary)]"
                }`}
                style={filterArea === key ? { backgroundColor: AREA_COLORS[key] } : {}}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Tag Filter + Sort */}
          <div className="flex flex-wrap items-center gap-2">
            {allTags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {allTags.map((tag) => (
                  <button
                    key={tag}
                    onClick={() => setFilterTag(filterTag === tag ? "" : tag)}
                    className={`rounded-full border px-2.5 py-1 text-xs transition ${
                      filterTag === tag
                        ? "border-[var(--color-primary)] bg-[var(--color-primary)] text-white"
                        : "border-[var(--border)] text-[var(--muted-foreground)] hover:border-[var(--color-primary)]"
                    }`}
                  >
                    #{tag}
                  </button>
                ))}
              </div>
            )}
            <div className="ml-auto">
              <select
                value={sort}
                onChange={(e) => setSort(e.target.value)}
                className="rounded-lg border border-[var(--border)] bg-[var(--background)] px-3 py-1.5 text-xs outline-none"
              >
                {SORT_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}

      {/* No Actions */}
      {actions.length === 0 && (
        <div className="mt-8 flex flex-col items-center justify-center rounded-2xl border border-[var(--border)] bg-[var(--card)] p-12 text-center">
          <p className="text-lg font-medium">아직 추천 액션이 없습니다</p>
          <p className="mt-2 text-sm text-[var(--muted-foreground)]">
            프로필 분석이 완료되면 맞춤 액션이 추천됩니다.
          </p>
        </div>
      )}

      {/* Action Cards */}
      <div className="mt-6 space-y-4">
        {filteredActions.map((action) => (
          <div
            key={action.id}
            className={`rounded-xl border bg-[var(--card)] p-5 transition ${
              action.is_completed
                ? "border-green-200 opacity-70"
                : "border-[var(--border)]"
            }`}
          >
            {/* Header */}
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  {action.target_area && (
                    <span
                      className="rounded px-2 py-0.5 text-xs font-medium text-white"
                      style={{
                        backgroundColor: AREA_COLORS[action.target_area] || "#6B7280",
                      }}
                    >
                      {AREA_LABELS[action.target_area] || action.target_area}
                    </span>
                  )}
                  {action.difficulty && (
                    <span
                      className={`rounded px-2 py-0.5 text-xs font-medium ${
                        DIFFICULTY_COLORS[action.difficulty] || ""
                      }`}
                    >
                      {DIFFICULTY_LABELS[action.difficulty] || action.difficulty}
                    </span>
                  )}
                  {action.impact_percent && (
                    <span className="text-xs font-bold text-[var(--color-primary)]">
                      +{action.impact_percent}%
                    </span>
                  )}
                </div>
                <h3
                  className={`mt-2 text-base font-bold ${
                    action.is_completed ? "line-through" : ""
                  }`}
                >
                  {action.title}
                </h3>
              </div>

              {/* Bookmark */}
              <button
                onClick={() => handleBookmark(action.id)}
                className="shrink-0 text-lg"
                title={action.is_bookmarked ? "북마크 해제" : "북마크"}
              >
                {action.is_bookmarked ? "\u2605" : "\u2606"}
              </button>
            </div>

            {/* Description */}
            {action.description && (
              <p className="mt-2 text-sm leading-relaxed text-[var(--muted-foreground)]">
                {action.description}
              </p>
            )}

            {/* Meta */}
            <div className="mt-3 flex flex-wrap items-center gap-3">
              {action.estimated_duration && (
                <span className="text-xs text-[var(--muted-foreground)]">
                  {action.estimated_duration}
                </span>
              )}
              {action.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-[var(--muted)] px-2 py-0.5 text-xs text-[var(--muted-foreground)]"
                >
                  #{tag}
                </span>
              ))}
            </div>

            {/* Actions */}
            <div className="mt-4 flex items-center gap-2">
              <button
                onClick={() => handleComplete(action.id)}
                className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
                  action.is_completed
                    ? "border border-green-500 text-green-600 hover:bg-green-50"
                    : "bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-dark)]"
                }`}
              >
                {action.is_completed ? "완료 취소" : "완료하기"}
              </button>
              {action.cta_label && !action.is_completed && (
                <button
                  onClick={() => {
                    if (action.cta_url) window.open(action.cta_url, "_blank");
                  }}
                  className="rounded-lg border border-[var(--border)] px-4 py-2 text-sm font-medium transition hover:border-[var(--color-primary)]"
                >
                  {action.cta_label}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
