import type { AppUser, AuthResponse, CarePlan, HistoryItem, IntakePayload, RuntimeConfig } from "../types/care";

const API_BASE =
  import.meta.env.VITE_API_BASE ??
  (window.location.port === "5173" ? "http://127.0.0.1:8010" : window.location.origin);
const TOKEN_KEY = "careroute_token";

export function sessionToken() {
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setSessionToken(token: string | null) {
  if (token) {
    window.localStorage.setItem(TOKEN_KEY, token);
  } else {
    window.localStorage.removeItem(TOKEN_KEY);
  }
}

async function request<T>(path: string, init?: RequestInit, token?: string | null): Promise<T> {
  const headers = new Headers(init?.headers ?? {});
  if (!headers.has("Content-Type") && init?.body) {
    headers.set("Content-Type", "application/json");
  }
  const activeToken = token ?? sessionToken();
  if (activeToken) {
    headers.set("Authorization", `Bearer ${activeToken}`);
  }
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  });
  if (!response.ok) {
    throw new Error(`API ${response.status}: ${await response.text()}`);
  }
  return response.json() as Promise<T>;
}

export async function register(payload: { full_name: string; email: string; password: string }) {
  return request<AuthResponse>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function login(payload: { email: string; password: string }) {
  return request<AuthResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function logout() {
  return request<{ ok: boolean }>("/api/auth/logout", { method: "POST" });
}

export async function fetchMe() {
  return request<AppUser>("/api/auth/me");
}

export async function fetchPublicConfig() {
  return request<RuntimeConfig>("/api/public-config", {}, null);
}

export async function saveProfile(payload: IntakePayload) {
  return request<IntakePayload>("/api/profile", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function loadHistory() {
  return request<HistoryItem[]>("/api/history");
}

export async function runCareRoute(payload: IntakePayload) {
  return request<CarePlan>("/api/run-care-route", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
