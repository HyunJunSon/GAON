/**
 * React Query 키 네이밍 규칙
 * - 배열 형태로 계층적으로 관리
 * - 서버 상태 키를 한 곳에서 관리하여 재사용성을 높임
 */
export const qk = {
  auth: {
    me: ['auth', 'me'] as const,
  },
  conversations: {
    list: (params?: string) => ['conversations', 'list', params] as const,
    detail: (id: string) => ['conversations', 'detail', id] as const,
  },
  analysis: {
    byId: (id: string) => ['analysis', id] as const,
  },
};