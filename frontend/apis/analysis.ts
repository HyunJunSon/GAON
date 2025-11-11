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

/** 음성 파일 업로드 및 STT 처리 */
export async function uploadAudio(audioBlob: Blob) {
  const formData = new FormData();
  formData.append('file', audioBlob, 'recording.webm');
  
  return apiFetch<StartAnalysisRes>('/api/conversation/audio', {
    method: 'POST',
    body: formData,
  });
}