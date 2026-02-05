"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth";

export function useAuthGuard() {
  const router = useRouter();
  const { accessToken } = useAuthStore();

  useEffect(() => {
    if (!accessToken) {
      router.replace("/auth");
    }
  }, [accessToken, router]);

  return { isAuthenticated: !!accessToken, accessToken };
}
