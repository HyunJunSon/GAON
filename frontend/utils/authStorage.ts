/**
 * 인증 토큰 저장/조회 유틸 (MVP: localStorage)
 * - 실제 서비스에선 httpOnly 쿠키 + 서버세션을 권장
 * - 프론트 단독 개발/목업에서는 localStorage로 간단히 처리
 */
const TOKEN_KEY = 'ga_access_token';

export const authStorage = {
  get(): string | null {
    try {
      return window.localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set(token: string) {
    try {
      window.localStorage.setItem(TOKEN_KEY, token);
    } catch {}
    // 미들웨어 보호용 가드 쿠키(로그인 되었다는 신호)
    document.cookie = 'ga_auth=1; path=/; max-age=86400; samesite=lax';
  },
  clear() {
    try {
      window.localStorage.removeItem(TOKEN_KEY);
    } catch {}
    // 보호 라우트 차단 신호
    document.cookie = 'ga_auth=; path=/; max-age=0; samesite=lax';
  },
};