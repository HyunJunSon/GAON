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

export type AnalysisStatus = 'queued' | 'processing' | 'ready' | 'completed' | 'failed';

export type AnalysisRes = {
  conversationId: string;
  status: AnalysisStatus;
  createdAt?: string;
  updatedAt?: string;
  statistics?: {
    user?: {
      top_words?: string[];
      word_count?: number;
      unique_words?: number;
      avg_sentence_length?: number;
    };
    others?: {
      word_count?: number;
      unique_words?: number;
      avg_sentence_length?: number;
    };
    comparison?: string;
  };
  style_analysis?: Record<
    string,
    {
      주요_관심사?: string;
      대화_비교_분석?: string;
      말투_특징_분석?: string;
      대화_성향_및_감정_표현?: string;
    }
  >;
  summary?: string;
  score?: number;
  confidence_score?: number;
  feedback: string;
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

/** 화자 매핑 관련 타입 */
export type SpeakerMapping = Record<string, string>;

export type SpeakerSegment = {
  speaker: number;
  speaker_name?: string;
  start: number;
  end: number;
  text: string;
};

export type SpeakerMappingResponse = {
  conversation_id: string;
  file_id: number;
  speaker_mapping: SpeakerMapping;
  user_mapping?: Record<string, number>;
  speaker_count: number;
  mapped_segments: SpeakerSegment[];
};

/** 화자 매핑 설정 */
export async function updateSpeakerMapping(
  conversationId: string, 
  speakerMapping: SpeakerMapping, 
  userMapping?: Record<string, number>
) {
  return apiFetch<{ 
    message: string;
    analysis_started?: boolean;
    can_proceed?: boolean;
  }>(`/api/conversation/audio/${conversationId}/speaker-mapping`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      speaker_mapping: speakerMapping,
      user_mapping: userMapping 
    }),
  });
}

/** 화자 매핑 조회 */
export async function getSpeakerMapping(conversationId: string) {
  return apiFetch<SpeakerMappingResponse>(`/api/conversation/audio/${conversationId}/speaker-mapping`, {
    method: 'GET',
  });
}

/** 사용자의 모든 분석 목록 조회 */
export type AnalysisListItem = {
  conversationId: string;
  title: string;
  summary?: string;
  score?: number;
  createdAt: string;
  status: 'ready' | 'processing' | 'failed';
};

export async function fetchAnalysisList() {
  return apiFetch<AnalysisListItem[]>('/api/analysis', {
    method: 'GET',
  });
}