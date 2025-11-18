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
export type AddFamilyRes = FamilyMember;

export async function getFamily(): Promise<GetFamilyRes> {
  return apiFetch<GetFamilyRes>('/api/family/members', { method: 'GET' });
}

export async function addFamily(payload: AddFamilyReq): Promise<AddFamilyRes> {
  return apiFetch<AddFamilyRes>('/api/family/members', {
    method: 'POST',
    json: payload,
  })
}

export async function removeFamily(memberId: string): Promise<{ ok: true }> {
  return apiFetch<{ ok: true }>(`/api/family/members/${memberId}`, {
    method: 'DELETE'
  })
}