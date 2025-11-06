const KEY = 'ga_last_conversation_id';
// 나중에 세션 단위로만 유지하고 싶으면 sessionStorage로 바꾸면 됨.
// FastAPI 실제 붙이면, 서버가 404/410을 주는 경우엔 clear()로 정리.
export const conversationIdStorage = {
  get(): string | null {
    try { return localStorage.getItem(KEY); } catch { return null; }
  },
  set(id: string) {
    try { localStorage.setItem(KEY, id); } catch {}
  },
  clear() {
    try { localStorage.removeItem(KEY); } catch {}
  },
};