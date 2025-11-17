// app/api/practice/_store.ts
export type SessionMsg = { role: 'user' | 'assistant'; content: string; ts: number };
export type PracticeSession = { id: string; conversationId: string; mode: 'chat'|'voice'|'hybrid'; participantIds: string[]; messages: SessionMsg[] };

type G = typeof globalThis & {
  __practice_participants__?: Array<{ id: string; name: string; relationship?: string }>;
  __practice_sessions__?: Record<string, PracticeSession>;
  __seeded__?: boolean;
};

const g = globalThis as G;

if (!g.__seeded__) {
  g.__practice_participants__ = [
    { id: 'p1', name: '엄마', relationship: 'parent' },
    { id: 'p2', name: '아들', relationship: 'child' },
    { id: 'p3', name: '아빠', relationship: 'parent' },
    { id: 'p4', name: '딸', relationship: 'daughter' },
  ];
  g.__practice_sessions__ = {};
  g.__seeded__ = true;
}

export const store = {
  participants(): Array<{ id: string; name: string; relationship?: string }> {
    return g.__practice_participants__!;
  },
  createSession(input: { conversationId: string; mode: 'chat'|'voice'|'hybrid'; participantIds: string[] }): PracticeSession {
    const id = 's_' + Math.random().toString(36).slice(2, 10);
    const s: PracticeSession = { id, messages: [], ...input };
    g.__practice_sessions__![id] = s;
    return s;
  },
  appendMessages(sessionId: string, msgs: SessionMsg[]) {
    const s = g.__practice_sessions__![sessionId];
    if (!s) throw new Error('NOT_FOUND');
    s.messages.push(...msgs);
  },
  getSession(sessionId: string): PracticeSession | undefined {
    return g.__practice_sessions__![sessionId];
  },
};