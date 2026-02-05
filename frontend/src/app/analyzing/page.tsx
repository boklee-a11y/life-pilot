"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth";
import { apiFetch } from "@/lib/api";

interface AnalysisStatus {
  progress: number;
  is_done: boolean;
  total: number;
  status_breakdown: Record<string, number>;
}

const STEPS = [
  { label: "프로필 데이터 수집 중", icon: "🔍" },
  { label: "AI 분석 진행 중", icon: "🤖" },
  { label: "결과 정리 중", icon: "📊" },
];

export default function AnalyzingPage() {
  const router = useRouter();
  const { accessToken } = useAuthStore();
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);
  const [statusText, setStatusText] = useState("분석을 시작하는 중...");

  useEffect(() => {
    if (!accessToken) {
      router.push("/auth");
      return;
    }

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
        // Retry on next interval
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [accessToken, router]);

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
            <span className="text-xl">
              {i < currentStep ? "✓" : step.icon}
            </span>
            <span className={`text-sm font-medium ${
              i < currentStep ? "text-green-600" : ""
            }`}>
              {step.label}
            </span>
            {i === currentStep && (
              <div className="ml-auto h-2 w-2 animate-pulse rounded-full bg-[var(--color-primary)]" />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
