import { authStorage } from "@/utils/authStorage";

/**
 * 공통 fetch 래퍼
 * - BASE_URL + path 결합
 * - JSON 응답/에러 정규화
 * - (추후) 인증 토큰/401 처리 추가 가능
 */
const BASE_URL = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || 'http://localhost:8000';

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
    // 필요시 credentials: 'include' 등 정책 추가
  })

  if (res.status === 401) {
    // 만료/무효 → 세션 초기화 및 로그인으로
    authStorage.clear()
    if (typeof window !== "undefined") window.location.href = "/login"
    throw new Error('Unauthorized')
  }
  
  // 2xx 외 에러 처리
  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      message = data?.message || message;
    } catch {}
    throw new Error(message);
  }
  
  // JSON 응답 파싱
  try {
    return (await res.json()) as T;
  } catch {
    // 빈 응답 등
    return undefined as T;
  }
}