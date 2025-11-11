import { apiFetch } from "./client";

export type FamilyMember = {
  id: string;
  name: string;
  email: string;
  joinedAt?: string;
}

export type GetFamilyRes = {
  members: FamilyMember[];
}

export type AddFamilyReq = { email: string }
export type AddFamilyRes = { ok: true, member?: FamilyMember };

export async function getFamily(): Promise<GetFamilyRes> {
  // 목업 /api/family 사용
  return apiFetch<GetFamilyRes>('/api/family', { method: 'GET' });
}

export async function addFamily(payload: AddFamilyReq): Promise<AddFamilyRes> {
  return apiFetch<AddFamilyRes>('/api/family', {
    method: 'POST',
    json: payload,
  })
}

export async function removeFamily(memberId: string): Promise<{ ok: true }> {
  return apiFetch<{ ok: true }>(`/api/family/${memberId}`, {
    method: 'DELETE'
  })
}