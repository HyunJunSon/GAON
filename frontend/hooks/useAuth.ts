'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { qk } from '@/constants/queryKeys';
import { getMe, login, signup } from '@/apis/auth';
import { authStorage } from '@/utils/authStorage';

export function useMe(enabled = true) {
  return useQuery({
    queryKey: qk.auth.me,
    queryFn: getMe,
    enabled: enabled && typeof window !== 'undefined' && !!authStorage.get(),
    staleTime: 0,                 // 캐시 비활성화
    gcTime: 0,                   // 가비지 컬렉션 즉시
    retry: false,
    refetchOnWindowFocus: true,   // 포커스 시 재요청
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
    mutationFn: async () => {
      // 백엔드 호출 없이 프론트엔드에서만 처리
      return Promise.resolve({ message: '로그아웃되었습니다.' });
    },
    onSuccess: () => {
      // 1. 토큰 삭제
      authStorage.clear();
      
      // 2. 모든 캐시 완전 제거
      qc.clear();
      qc.removeQueries();
      qc.invalidateQueries();
      
      // 3. localStorage 완전 정리
      if (typeof window !== 'undefined') {
        localStorage.clear();
        sessionStorage.clear();
        
        // 4. 강제 페이지 리로드로 완전 초기화
        window.location.href = '/login';
      }
    },
    onError: () => {
      // 에러가 발생해도 강제 로그아웃
      authStorage.clear();
      if (typeof window !== 'undefined') {
        localStorage.clear();
        window.location.href = '/login';
      }
    }
  });
}