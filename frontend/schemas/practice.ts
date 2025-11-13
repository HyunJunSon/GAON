// schemas/practice.ts
export type PracticeMode = 'new' | 'replay';

export type PracticeParticipant = {
  id: string;
  name: string;
  relationship?: string; // 예: 엄마/아빠/아들 등
};

export type StartPracticeReq = {
  conversationId: string;
  mode: PracticeMode;
  participantIds: string[];
};

export type StartPracticeRes = {
  sessionId: string;
};

export type FinishPracticeReq = {
  messages: Array<{ role: 'user' | 'assistant' | 'system'; content: string; ts: number }>;
  // 추후 음성 메타 포함 가능
};

export type FinishPracticeRes = {
  ok: true;
  sessionId: string; // 결과 페이지와 동일
};

export type PracticeResult = {
  sessionId: string;
  score: number;
  strengths: string[];
  improvements: string[];
  summary: string;
  createdAt: string;
};