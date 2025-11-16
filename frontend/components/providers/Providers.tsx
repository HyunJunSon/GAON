'use client';
/**
 * 전역 Provider 컴포넌트
 * - React Query: 서버 상태(요청/캐시/에러)를 전역에서 관리
 * - Global WebSocket: 분석 완료 알림을 전역에서 관리
 * - children: 모든 페이지를 감싸도록 app/layout.tsx에서 사용
**/
import { PropsWithChildren, useState } from "react";
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useGlobalWebSocket } from '@/hooks/useGlobalWebSocket';

function GlobalNotificationProvider({ children }: PropsWithChildren) {
  // 전역 알림 시스템 활성화
  useGlobalWebSocket();
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