/**
 * React Query 키 네이밍 규칙
 * - 배열 형태로 계층적으로 관리
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
    summary: (id: string) => ['analysis', 'summary', id] as const,
    emotion: (id: string) => ['analysis', 'emotion', id] as const,
    transcript: (id: string) => ['analysis', 'transcript', id] as const,
  },
};