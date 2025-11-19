import { apiFetch } from './client';

// 백엔드 스펙에 맞춘 타입 정의
export type User = {
  id: number;
  email: string;
  name: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  username: string;
};

export type SignupResponse = {
  user_id: number;
};

export async function login(payload: { email: string; password: string }) {
  // OAuth2PasswordRequestForm 형식으로 전송
  const formData = new FormData();
  formData.append('username', payload.email); // OAuth2에서는 username 필드 사용
  formData.append('password', payload.password);
  
  const response = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Login failed');
  }
  
  return response.json() as Promise<LoginResponse>;
}

export async function signup(payload: {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
  termsAgreed: boolean;
}) {
  return apiFetch<SignupResponse>('http://localhost:8000/api/auth/signup', {
    method: 'POST',
    json: payload,
    auth: false,
  });
}

export async function getMe() {
  return apiFetch<User>('http://localhost:8000/api/auth/me', { method: 'GET' });
}