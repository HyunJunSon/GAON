'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { qk } from '@/constants/queryKeys';
import { getMe, login, logout, signup } from '@/apis/auth';
import { authStorage } from '@/utils/authStorage';

export function useMe(enabled = true) {
  // 토큰이 없으면 호출하지 않음(선택 로직)
  const hasToken = typeof window !== 'undefined' && !!authStorage.get();

  return useQuery({
    queryKey: qk.auth.me,
    queryFn: getMe,
    enabled: enabled && hasToken, // 로그인 상태에서만 호출
    staleTime: 1000 * 60,         // 1분 캐시
  });
}

export function useLogin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: login,
    onSuccess: (data) => {
      // 1) 토큰 저장 (백엔드 응답 형식에 맞춤)
      authStorage.set(data.access_token);
      // 2) me 정보 무효화하여 재요청
      qc.invalidateQueries({ queryKey: qk.auth.me });
    },
  });
}

export function useSignup() {
  return useMutation({ mutationFn: signup });
}

export function useLogout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: logout,
    onSuccess: () => {
      authStorage.clear();
      qc.removeQueries({ queryKey: qk.auth.me }); // 세션 정보 제거
      if (typeof window !== 'undefined') {
        window.location.replace('/login'); // 로그인으로 이동
      }
    },
  });
}