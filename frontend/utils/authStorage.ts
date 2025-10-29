/**
 * 인증 토큰 저장/조회 유틸 (MVP: localStorage)
 * - 실제 서비스에선 httpOnly 쿠키 + 서버세션을 권장
 * - 프론트 단독 개발/목업에서는 localStorage로 간단히 처리
 */
const TOKEN_KEY = 'mock-token-abc123';

export const authStorage = {
  get() {
    if (typeof window === 'undefined') return null;
    return window.localStorage.getItem(TOKEN_KEY);
  },
  set(token: string) {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(TOKEN_KEY, token);
  },
  clear() {
    if (typeof window === 'undefined') return;
    window.localStorage.removeItem(TOKEN_KEY);
  },
};