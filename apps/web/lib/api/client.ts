/**
 * lib/api/client.ts
 * =================
 * Centralized, resilient HTTP client for FastAPI communication.
 */

import { ApiClientError } from "./types";

const DEFAULT_BASE_URL = "http://127.0.0.1:8000";
const DEFAULT_TIMEOUT_MS = 15000;

export function getApiBaseUrl(): string {
  if (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_BASE_URL) {
    return process.env.NEXT_PUBLIC_API_BASE_URL.replace(/\/+$/, "");
  }
  return DEFAULT_BASE_URL;
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit & { timeoutMs?: number } = {}
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const headers: Record<string, string> = {
    Accept: "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  if (options.body && typeof options.body === "string" && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorDetail: unknown;
      try {
        const json = await response.json();
        errorDetail = json.detail || json;
      } catch {
        errorDetail = await response.text().catch(() => "Unknown error");
      }

      const message =
        typeof errorDetail === "string"
          ? errorDetail
          : `API request failed with status ${response.status} (${response.statusText})`;

      throw new ApiClientError(message, response.status, errorDetail);
    }

    // Parse JSON
    return (await response.json()) as T;
  } catch (error: unknown) {
    clearTimeout(timeoutId);

    if (error instanceof ApiClientError) {
      throw error;
    }

    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiClientError(
        `Request to ${endpoint} timed out after ${timeoutMs}ms`,
        408
      );
    }

    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new ApiClientError(
        `Unable to reach Sentinel API server at ${baseUrl}. Ensure FastAPI is running on port 8000.`,
        0,
        error
      );
    }

    throw new ApiClientError(
      error instanceof Error ? error.message : "Unexpected network error occurred",
      500,
      error
    );
  }
}
