import { apiFetch } from "./client";

export type StartAnalysisRes = {
  conversationId: string;
  status: 'queued' | 'processing' | 'ready';
}

export type StartAnalysisResSnake = {
  conversation_id: string;
  status: 'queued' | 'processing' | 'ready';
};

export type StartAnalysisAny = StartAnalysisRes | StartAnalysisResSnake;

export type AnalysisStatus = 'queued' | 'processing' | 'ready' | 'failed';

export type AnalysisRes = {
  conversationId: string;
  status: AnalysisStatus;
  updatedAt?: string;
  summary?: { bullets: string[] };
  emotion?: { series: Array<{ label: string; value: number }> };
  dialog?: { raw: string };
  errorMessage?: string | null;
}

export function getConversationId(res: StartAnalysisAny): string {
  if ('conversationId' in res && typeof res.conversationId === 'string') {
    return res.conversationId
  }
  if ('conversation_id' in res && typeof res.conversation_id === 'string') {
    return res.conversation_id;
  }
  throw new Error('서버 응답에 conversationId가 없습니다.');
}
/** 분석 시작(파일 업로드 포함) */
export async function startAnalysis(form: FormData) {
  // JWT 토큰은 apiFetch에서 자동으로 헤더에 포함됨
  return apiFetch<StartAnalysisRes>('/api/conversations/analyze', {
    method: 'POST',
    body: form,
  });
}

/** 특정 ID 분석 결과 조회 */
export async function fetchAnalysis(conversationId: string) {
  return apiFetch<AnalysisRes>(`/api/analysis/${conversationId}`, {
    method: 'GET',
  });
}