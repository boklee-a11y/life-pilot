"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthGuard } from "@/hooks/useAuthGuard";
import { useToast } from "@/components/Toast";
import { apiFetch } from "@/lib/api";

const PLATFORM_PRESETS = [
  { id: "linkedin", label: "LinkedIn", placeholder: "https://linkedin.com/in/username" },
  { id: "github", label: "GitHub", placeholder: "https://github.com/username" },
  { id: "velog", label: "Velog", placeholder: "https://velog.io/@username" },
  { id: "tistory", label: "Tistory", placeholder: "https://username.tistory.com" },
  { id: "dribbble", label: "Dribbble", placeholder: "https://dribbble.com/username" },
  { id: "behance", label: "Behance", placeholder: "https://behance.net/username" },
];

const JOB_CATEGORIES = [
  { id: "dev", label: "개발" },
  { id: "design", label: "디자인" },
  { id: "pm", label: "PM" },
  { id: "marketing", label: "마케팅" },
  { id: "data", label: "데이터" },
  { id: "other", label: "기타" },
];

interface UrlEntry {
  url: string;
  platform: string;
}

export default function OnboardingPage() {
  const router = useRouter();
  const { accessToken, isAuthenticated } = useAuthGuard();
  const { toast } = useToast();
  const [step, setStep] = useState(1);
  const [urls, setUrls] = useState<UrlEntry[]>([]);
  const [currentUrl, setCurrentUrl] = useState("");
  const [currentPlatform, setCurrentPlatform] = useState("");
  const [jobCategory, setJobCategory] = useState("");
  const [yearsOfExperience, setYearsOfExperience] = useState(1);
  const [loading, setLoading] = useState(false);

  const addUrl = (url: string, platform: string) => {
    if (!url.trim()) return;
    setUrls([...urls, { url: url.trim(), platform }]);
    setCurrentUrl("");
    setCurrentPlatform("");
  };

  const removeUrl = (index: number) => {
    setUrls(urls.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (urls.length === 0 || !jobCategory) return;
    setLoading(true);

    try {
      // 1. Save profile
      await apiFetch("/onboarding/profile", {
        method: "POST",
        body: JSON.stringify({
          job_category: jobCategory,
          years_of_experience: yearsOfExperience,
        }),
        token: accessToken!,
      });

      // 2. Register all URLs
      for (const entry of urls) {
        await apiFetch("/sources", {
          method: "POST",
          body: JSON.stringify({ url: entry.url, platform: entry.platform || null }),
          token: accessToken!,
        });
      }

      router.push("/analyzing");
    } catch (err) {
      toast("error", err instanceof Error ? err.message : "오류가 발생했습니다. 다시 시도해주세요.");
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated) return null;

  return (
    <div className="mx-auto max-w-lg pt-8">
      {/* Progress Bar */}
      <div className="mb-8 flex gap-2">
        {[1, 2, 3].map((s) => (
          <div
            key={s}
            className={`h-1.5 flex-1 rounded-full transition ${
              s <= step ? "bg-[var(--color-primary)]" : "bg-[var(--muted)]"
            }`}
          />
        ))}
      </div>

      {/* Step 1: URL 입력 */}
      {step === 1 && (
        <div>
          <h2 className="text-2xl font-bold">프로필 URL을 입력하세요</h2>
          <p className="mt-2 text-[var(--muted-foreground)]">
            어떤 플랫폼이든 괜찮아요. 최소 1개 이상 입력해주세요.
          </p>

          {/* Platform Presets */}
          <div className="mt-6 flex flex-wrap gap-2">
            {PLATFORM_PRESETS.map((p) => (
              <button
                key={p.id}
                onClick={() => {
                  setCurrentPlatform(p.id);
                  setCurrentUrl("");
                }}
                className={`rounded-lg border px-3 py-1.5 text-sm transition ${
                  currentPlatform === p.id
                    ? "border-[var(--color-primary)] bg-[var(--color-primary)] text-white"
                    : "border-[var(--border)] hover:border-[var(--color-primary)]"
                }`}
              >
                {p.label}
              </button>
            ))}
            <button
              onClick={() => setCurrentPlatform("other")}
              className={`rounded-lg border px-3 py-1.5 text-sm transition ${
                currentPlatform === "other"
                  ? "border-[var(--color-primary)] bg-[var(--color-primary)] text-white"
                  : "border-[var(--border)] hover:border-[var(--color-primary)]"
              }`}
            >
              기타 URL
            </button>
          </div>

          {/* URL Input */}
          {currentPlatform && (
            <div className="mt-4 flex gap-2">
              <input
                type="url"
                placeholder={
                  PLATFORM_PRESETS.find((p) => p.id === currentPlatform)?.placeholder ||
                  "https://example.com/profile"
                }
                value={currentUrl}
                onChange={(e) => setCurrentUrl(e.target.value)}
                className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--background)] px-4 py-3 text-sm outline-none focus:border-[var(--color-primary)]"
              />
              <button
                onClick={() => addUrl(currentUrl, currentPlatform)}
                disabled={!currentUrl.trim()}
                className="rounded-lg bg-[var(--color-primary)] px-4 py-3 text-sm font-medium text-white disabled:opacity-50"
              >
                추가
              </button>
            </div>
          )}

          {/* Added URLs */}
          {urls.length > 0 && (
            <div className="mt-6 space-y-2">
              {urls.map((entry, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--muted)] px-4 py-3"
                >
                  <div className="min-w-0 flex-1">
                    <span className="mr-2 rounded bg-[var(--color-primary)] px-2 py-0.5 text-xs text-white">
                      {entry.platform}
                    </span>
                    <span className="text-sm truncate">{entry.url}</span>
                  </div>
                  <button
                    onClick={() => removeUrl(i)}
                    className="ml-2 text-sm text-[var(--muted-foreground)] hover:text-red-500"
                  >
                    삭제
                  </button>
                </div>
              ))}
            </div>
          )}

          <p className="mt-4 text-sm text-[var(--muted-foreground)]">
            프로필을 추가할수록 분석이 정교해집니다.
          </p>

          <button
            onClick={() => setStep(2)}
            disabled={urls.length === 0}
            className="mt-6 w-full rounded-lg bg-[var(--color-primary)] py-3 text-sm font-semibold text-white transition hover:bg-[var(--color-primary-dark)] disabled:opacity-50"
          >
            다음
          </button>
        </div>
      )}

      {/* Step 2: 직군/연차 선택 */}
      {step === 2 && (
        <div>
          <h2 className="text-2xl font-bold">직군과 경력을 선택하세요</h2>
          <p className="mt-2 text-[var(--muted-foreground)]">
            동일 직군 대비 정확한 포지셔닝을 위해 필요합니다.
          </p>

          <div className="mt-6">
            <label className="text-sm font-medium">직군</label>
            <div className="mt-2 grid grid-cols-3 gap-2">
              {JOB_CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setJobCategory(cat.id)}
                  className={`rounded-lg border py-3 text-sm font-medium transition ${
                    jobCategory === cat.id
                      ? "border-[var(--color-primary)] bg-[var(--color-primary)] text-white"
                      : "border-[var(--border)] hover:border-[var(--color-primary)]"
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-6">
            <label className="text-sm font-medium">
              경력 연차: {yearsOfExperience}년
            </label>
            <input
              type="range"
              min={0}
              max={20}
              value={yearsOfExperience}
              onChange={(e) => setYearsOfExperience(Number(e.target.value))}
              className="mt-2 w-full accent-[var(--color-primary)]"
            />
            <div className="flex justify-between text-xs text-[var(--muted-foreground)]">
              <span>신입</span>
              <span>10년</span>
              <span>20년+</span>
            </div>
          </div>

          <div className="mt-8 flex gap-3">
            <button
              onClick={() => setStep(1)}
              className="flex-1 rounded-lg border border-[var(--border)] py-3 text-sm font-medium"
            >
              이전
            </button>
            <button
              onClick={() => setStep(3)}
              disabled={!jobCategory}
              className="flex-1 rounded-lg bg-[var(--color-primary)] py-3 text-sm font-semibold text-white disabled:opacity-50"
            >
              다음
            </button>
          </div>
        </div>
      )}

      {/* Step 3: 확인 및 분석 시작 */}
      {step === 3 && (
        <div>
          <h2 className="text-2xl font-bold">분석을 시작할까요?</h2>
          <p className="mt-2 text-[var(--muted-foreground)]">
            입력한 정보를 확인하고 분석을 시작합니다.
          </p>

          <div className="mt-6 space-y-3 rounded-xl border border-[var(--border)] bg-[var(--card)] p-6">
            <div>
              <span className="text-sm text-[var(--muted-foreground)]">등록된 프로필</span>
              <div className="mt-1 space-y-1">
                {urls.map((entry, i) => (
                  <div key={i} className="text-sm">
                    <span className="mr-2 rounded bg-[var(--color-primary)] px-2 py-0.5 text-xs text-white">
                      {entry.platform}
                    </span>
                    {entry.url}
                  </div>
                ))}
              </div>
            </div>
            <div>
              <span className="text-sm text-[var(--muted-foreground)]">직군</span>
              <p className="text-sm font-medium">
                {JOB_CATEGORIES.find((c) => c.id === jobCategory)?.label}
              </p>
            </div>
            <div>
              <span className="text-sm text-[var(--muted-foreground)]">경력</span>
              <p className="text-sm font-medium">{yearsOfExperience}년</p>
            </div>
          </div>

          <div className="mt-8 flex gap-3">
            <button
              onClick={() => setStep(2)}
              className="flex-1 rounded-lg border border-[var(--border)] py-3 text-sm font-medium"
            >
              이전
            </button>
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="flex-1 rounded-lg bg-[var(--color-primary)] py-3 text-sm font-semibold text-white disabled:opacity-50"
            >
              {loading ? "분석 시작 중..." : "분석 시작하기"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
