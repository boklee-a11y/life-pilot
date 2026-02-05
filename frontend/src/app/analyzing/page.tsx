"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthGuard } from "@/hooks/useAuthGuard";
import { useToast } from "@/components/Toast";
import { apiFetch } from "@/lib/api";

interface AnalysisStatus {
  progress: number;
  is_done: boolean;
  total: number;
  status_breakdown: Record<string, number>;
}

const STEPS = [
  { label: "프로필 데이터 수집 중", icon: "1" },
  { label: "AI 분석 진행 중", icon: "2" },
  { label: "결과 정리 중", icon: "3" },
];

export default function AnalyzingPage() {
  const router = useRouter();
  const { accessToken, isAuthenticated } = useAuthGuard();
  const { toast } = useToast();
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);
  const [statusText, setStatusText] = useState("분석을 시작하는 중...");
  const [failCount, setFailCount] = useState(0);

  useEffect(() => {
    if (!accessToken) return;

    // Start analysis
    apiFetch("/analysis/run", {
      method: "POST",
      token: accessToken,
    }).catch(() => {
      // Analysis may already be running
    });

    // Poll for status
    const interval = setInterval(async () => {
      try {
        const status = await apiFetch<AnalysisStatus>("/analysis/status", {
          token: accessToken,
        });

        setProgress(status.progress);
        setFailCount(0);

        // Determine current step based on status
        const breakdown = status.status_breakdown;
        if (breakdown.scraping && breakdown.scraping > 0) {
          setCurrentStep(0);
          setStatusText("프로필 페이지 데이터를 수집하고 있어요");
        } else if (breakdown.parsing && breakdown.parsing > 0) {
          setCurrentStep(1);
          setStatusText("AI가 커리어 데이터를 분석하고 있어요");
        } else if (status.progress > 0) {
          setCurrentStep(2);
          setStatusText("분석 결과를 정리하고 있어요");
        }

        if (status.is_done) {
          clearInterval(interval);
          setProgress(100);
          setCurrentStep(2);
          setStatusText("분석이 완료되었어요!");

          // Navigate to dashboard after brief delay
          setTimeout(() => router.push("/dashboard"), 1500);
        }
      } catch {
        setFailCount((prev) => {
          const next = prev + 1;
          if (next >= 10) {
            clearInterval(interval);
            toast("error", "분석 상태를 확인할 수 없습니다. 대시보드에서 확인해주세요.");
            setTimeout(() => router.push("/dashboard"), 2000);
          }
          return next;
        });
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [accessToken, router, toast]);

  if (!isAuthenticated) return null;

  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center text-center">
      {/* Animated Spinner */}
      <div className="relative mb-8 h-32 w-32">
        <svg className="h-32 w-32 -rotate-90" viewBox="0 0 120 120">
          <circle
            cx="60"
            cy="60"
            r="50"
            stroke="var(--muted)"
            strokeWidth="8"
            fill="none"
          />
          <circle
            cx="60"
            cy="60"
            r="50"
            stroke="var(--color-primary)"
            strokeWidth="8"
            fill="none"
            strokeLinecap="round"
            strokeDasharray={`${progress * 3.14} 314`}
            className="transition-all duration-500"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-2xl font-bold text-[var(--color-primary)]">
            {progress}%
          </span>
        </div>
      </div>

      <h1 className="text-2xl font-bold">{statusText}</h1>

      <p className="mt-2 text-sm text-[var(--muted-foreground)]">
        보통 30초 정도 소요됩니다
      </p>

      {/* Step Indicators */}
      <div className="mt-10 w-full max-w-sm space-y-4">
        {STEPS.map((step, i) => (
          <div
            key={i}
            className={`flex items-center gap-3 rounded-lg border p-4 transition-all ${
              i === currentStep
                ? "border-[var(--color-primary)] bg-[var(--color-primary)]/5"
                : i < currentStep
                  ? "border-green-500/30 bg-green-500/5"
                  : "border-[var(--border)] opacity-50"
            }`}
          >
            <span
              className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${
                i < currentStep
                  ? "bg-green-500 text-white"
                  : i === currentStep
                    ? "bg-[var(--color-primary)] text-white"
                    : "bg-[var(--muted)] text-[var(--muted-foreground)]"
              }`}
            >
              {i < currentStep ? "\u2713" : step.icon}
            </span>
            <span className={`text-sm font-medium ${
              i < currentStep ? "text-green-600 dark:text-green-400" : ""
            }`}>
              {step.label}
            </span>
            {i === currentStep && (
              <div className="ml-auto h-2 w-2 animate-pulse rounded-full bg-[var(--color-primary)]" />
            )}
          </div>
        ))}
      </div>

      {failCount >= 5 && (
        <p className="mt-6 text-xs text-[var(--muted-foreground)]">
          서버 응답이 느립니다. 잠시만 기다려주세요...
        </p>
      )}
    </div>
  );
}
