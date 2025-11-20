'use client';
/**
 * 전역 Provider 컴포넌트
 * - React Query: 서버 상태(요청/캐시/에러)를 전역에서 관리
 * - Global WebSocket: 분석 완료 알림을 전역에서 관리
 * - User WebSocket: 사용자별 실시간 알림을 전역에서 관리
 * - children: 모든 페이지를 감싸도록 app/layout.tsx에서 사용
**/
import { PropsWithChildren, useState, useEffect } from "react";
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useGlobalWebSocket } from '@/hooks/useGlobalWebSocket';
import { useUserWebSocket } from '@/hooks/useUserWebSocket';

function GlobalNotificationProvider({ children }: PropsWithChildren) {
  const [userEmail, setUserEmail] = useState<string>();
  
  // 사용자 이메일 가져오기 (토큰으로 /me API 호출)
  useEffect(() => {
    const fetchUserEmail = async () => {
      try {
        const token = localStorage.getItem('authToken');
        if (!token) return;
        
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/me`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const user = await response.json();
          setUserEmail(user.email);
        }
      } catch (error) {
        console.error('사용자 정보 가져오기 실패:', error);
      }
    };
    
    fetchUserEmail();
  }, []);
  
  // 전역 알림 시스템 활성화
  useGlobalWebSocket();
  useUserWebSocket(userEmail);
  
  return <>{children}</>;
}

export default function Providers({ children }: PropsWithChildren) {
  // QueryClient는 1개 인스턴스를 앱 수명 동안 유지
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // 실패 시 재시도 횟수/캐시시간 등 기본 설정
            retry: 1,
            refetchOnWindowFocus: false,
          }
        }
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <GlobalNotificationProvider>
        {children}
      </GlobalNotificationProvider>
    </QueryClientProvider>
  )
}