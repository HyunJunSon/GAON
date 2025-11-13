// apis/practice.ts
import { apiFetch } from '@/apis/client';
import type {
  PracticeParticipant,
  StartPracticeReq, StartPracticeRes,
  FinishPracticeReq, FinishPracticeRes,
  PracticeResult
} from '@/schemas/practice';

export async function fetchParticipants(): Promise<{ participants: PracticeParticipant[] }> {
  return apiFetch('/api/practice/participants', { method: 'GET' });
}

export async function startPractice(body: StartPracticeReq): Promise<StartPracticeRes> {
  return apiFetch('/api/practice/session', { method: 'POST', json: body });
}

export async function finishPractice(sessionId: string, body: FinishPracticeReq): Promise<FinishPracticeRes> {
  return apiFetch(`/api/practice/session/${sessionId}/finish`, { method: 'POST', json: body });
}

export async function fetchPracticeResult(sessionId: string): Promise<PracticeResult> {
  return apiFetch(`/api/practice/result/${sessionId}`, { method: 'GET' });
}