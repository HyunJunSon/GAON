import { apiFetch } from "./client";

export type StartAnalysisRes = {
  conversationId: string;
  status: 'queued' | 'processing' | 'ready';
}

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

/** 분석 시작(파일 업로드 포함) */
export async function startAnalysis(form: FormData) {
  // FormData 사용 시 Content-Type은 브라우저가 자동 설정
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