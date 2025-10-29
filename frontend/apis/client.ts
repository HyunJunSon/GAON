/**
 * 공통 fetch 래퍼
 * - BASE_URL + path 결합
 * - JSON 응답/에러 정규화
 * - (추후) 인증 토큰/401 처리 추가 가능
 */
const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, '') || '';

type FetchOptions = RequestInit & { json?: unknown };

export async function apiFetch<T>(
  path: string,
  options: FetchOptions = {}
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const headers = new Headers(options.headers);

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