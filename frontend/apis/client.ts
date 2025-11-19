import { authStorage } from "@/utils/authStorage";

/**
 * 공통 fetch 래퍼
 * - 환경변수 기반 URL 처리
 * - JSON 응답/에러 정규화
 * - 인증 토큰/401 처리
 */
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

type FetchOptions = RequestInit & { json?: unknown, auth?: boolean };

export async function apiFetch<T>(
  path: string,
  options: FetchOptions = {}
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const headers = new Headers(options.headers);

  // 토큰이 있다면 Authorization 헤더 주입
  if (options.auth !== false) {
    const token = authStorage.get();
    if (token && !headers.has('Authorization')) {
      headers.set('Authorization', `Bearer ${token}`);
    }
  }
  
  // JSON 요청 자동 처리
  if (options.json != undefined) {
    headers.set('Content-Type', 'application/json');
  }

  const res = await fetch(url, {
    ...options,
    headers,
    body: options.json !== undefined ? JSON.stringify(options.json) : options.body,
  })

  if (res.status === 401) {
    authStorage.clear()
    if (typeof window !== "undefined") window.location.href = "/login"
    throw new Error('Unauthorized')
  }
  
  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      message = data?.message || data?.detail || message;
    } catch {}
    throw new Error(message);
  }
  
  try {
    return (await res.json()) as T;
  } catch {
    return undefined as T;
  }
}