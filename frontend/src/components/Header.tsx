"use client";

import Link from "next/link";
import { useAuthStore } from "@/stores/auth";

export function Header() {
  const { user, logout } = useAuthStore();

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-[var(--card)]">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
        <Link href="/" className="text-lg font-bold text-[var(--color-primary)]">
          Life_Pilot
        </Link>

        <nav className="flex items-center gap-4">
          {user ? (
            <>
              <Link
                href="/dashboard"
                className="text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
              >
                대시보드
              </Link>
              <Link
                href="/actions"
                className="text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
              >
                액션플랜
              </Link>
              <button
                onClick={logout}
                className="text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
              >
                로그아웃
              </button>
            </>
          ) : (
            <Link
              href="/auth"
              className="rounded-lg bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-primary-dark)]"
            >
              시작하기
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
