import { apiFetch } from './client';

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
  const formData = new FormData();
  formData.append('username', payload.email);
  formData.append('password', payload.password);
  
  return apiFetch<LoginResponse>('/api/auth/login', {
    method: 'POST',
    body: formData,
    auth: false,
  });
}

export async function signup(payload: {
  name: string;
  email: string;
  birthdate: string;
  gender: string;
  password: string;
  confirmPassword: string;
  termsAgreed: boolean;
}) {
  return apiFetch<SignupResponse>('/api/auth/signup', {
    method: 'POST',
    json: payload,
    auth: false,
  });
}

export async function getMe() {
  return apiFetch<User>('/api/auth/me', { method: 'GET' });
}