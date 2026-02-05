import { useAuthStore } from "@/stores/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FetchOptions extends RequestInit {
  token?: string;
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function apiFetch<T>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<T> {
  const { token, headers: customHeaders, ...rest } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((customHeaders as Record<string, string>) || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}/api/v1${endpoint}`, {
    headers,
    ...rest,
  });

  if (!res.ok) {
    // 401: auto-logout
    if (res.status === 401) {
      useAuthStore.getState().logout();
    }

    const error = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new ApiError(
      error.detail || `HTTP ${res.status}`,
      res.status
    );
  }

  if (res.status === 204) return null as T;
  return res.json();
}
