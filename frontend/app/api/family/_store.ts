// app/api/family/_store.ts
export type Member = {
  id: string;
  name: string;
  email: string;
  role?: string;
  joinedAt?: string;
};

// 전역(모듈 캐시)에 보관해서 /api/family 와 /api/family/[id] 가 같은 배열을 공유
const g = globalThis as any;

if (!g.__family_members__) {
  g.__family_members__ = [
    { id: 'u1', name: '엄마', email: 'mom@example.com', role: 'parent', joinedAt: new Date().toISOString() },
    { id: 'u2', name: '아들', email: 'son@example.com', role: 'child',  joinedAt: new Date().toISOString() },
  ] as Member[];
}

export function getMembers(): Member[] {
  return g.__family_members__ as Member[];
}

export function setMembers(next: Member[]) {
  g.__family_members__ = next;
}