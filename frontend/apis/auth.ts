import { apiFetch } from './client';

// 서버 응답 타입 예시 — 백엔드 스펙에 맞춰 조정예정
export type User = {
  id: string;
  name: string;
  email: string;
};

export type LoginResponse = {
  accessToken: string;
  user: User;
};

export type SignupResponse = {
  accessToken: string;   // 가입 후 자동 로그인 플로우라면 토큰 포함
  user: User;
};

export async function login(payload: { email: string; password: string }) {
  // 실제 엔드포인트에 맞춰 경로/메서드 수정
  return apiFetch<LoginResponse>('/api/auth/login', {
    method: 'POST',
    json: payload,
  });
}

export async function signup(payload: {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
}) {
  return apiFetch<SignupResponse>('/api/auth/signup', {
    method: 'POST',
    json: payload,
  });
}

export async function getMe() {
  return apiFetch<User>('/auth/me', { method: 'GET' });
}

export async function logout() {
  // 서버 세션을 쓴다면 여기서 세션 종료 API 호출
  // 프론트만 있을 땐 토큰 삭제만 처리
  return Promise.resolve();
}