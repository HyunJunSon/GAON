'use client';

import { useEffect, useRef } from 'react';
import { useNotificationStore } from '@/lib/notificationStore';

export function useUserWebSocket(userEmail?: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const { addNotification } = useNotificationStore();

  useEffect(() => {
    if (!userEmail) return;

    const connectWebSocket = () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const wsUrl = apiUrl.replace('http', 'ws') + `/ws/user/${encodeURIComponent(userEmail)}`;
        
        wsRef.current = new WebSocket(wsUrl);
        
        wsRef.current.onopen = () => {
          console.log(`🔗 사용자 WebSocket 연결됨: ${userEmail}`);
        };
        
        wsRef.current.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            
            if (message.type === 'family_invite') {
              // 가족 초대 알림
              addNotification({
                type: 'info',
                title: message.data.title,
                message: message.data.message,
                actionType: 'family_invite',
                inviteId: message.data.memberId,
                inviterName: message.data.inviterName,
                familyName: message.data.familyName
              });
            }
          } catch (error) {
            console.error('WebSocket 메시지 파싱 오류:', error);
          }
        };
        
        wsRef.current.onclose = () => {
          console.log(`🔌 사용자 WebSocket 연결 끊어짐: ${userEmail}`);
        };
        
        wsRef.current.onerror = (error) => {
          console.error('사용자 WebSocket 오류:', error);
        };
      } catch (error) {
        console.error('사용자 WebSocket 연결 실패:', error);
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [userEmail, addNotification]);
}
