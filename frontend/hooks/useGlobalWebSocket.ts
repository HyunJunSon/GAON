import { useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useNotificationStore } from '@/lib/notificationStore';

interface GlobalWebSocketManager {
  connections: Map<string, WebSocket>;
  addConnection: (conversationId: string) => void;
  removeConnection: (conversationId: string) => void;
}

// 전역 WebSocket 관리자 (싱글톤)
const globalWsManager: GlobalWebSocketManager = {
  connections: new Map(),
  addConnection: function(conversationId: string) {
    if (this.connections.has(conversationId)) return;

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const wsUrl = apiUrl.replace('http', 'ws') + `/ws/analysis/${conversationId}`;
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log(`전역 WebSocket 연결됨: ${conversationId}`);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        
        if (message.type === 'analysis_complete') {
          // 전역 이벤트 발생
          window.dispatchEvent(new CustomEvent('gaon-analysis-complete', {
            detail: { conversationId, data: message.data }
          }));
        }
      } catch (error) {
        console.error('WebSocket 메시지 파싱 오류:', error);
      }
    };

    ws.onclose = () => {
      console.log(`WebSocket 연결 종료: ${conversationId}`);
      this.connections.delete(conversationId);
    };

    this.connections.set(conversationId, ws);
  },
  
  removeConnection: function(conversationId: string) {
    const ws = this.connections.get(conversationId);
    if (ws) {
      ws.close();
      this.connections.delete(conversationId);
    }
  }
};

export function useGlobalWebSocket(conversationId?: string) {
  const router = useRouter();
  const { addNotification } = useNotificationStore();
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // conversationId가 없으면 연결하지 않음
    if (!conversationId) return;

    // WebSocket 연결 설정
    const connectWebSocket = () => {
      try {
        const wsUrl = process.env.NODE_ENV === 'production' 
          ? `wss://gaon.wyhil.com/ws/analysis/${conversationId}` 
          : `ws://localhost:8000/ws/analysis/${conversationId}`;
        
        wsRef.current = new WebSocket(wsUrl);
        
        wsRef.current.onopen = () => {
          console.log(`🔗 WebSocket 연결됨: ${conversationId}`);
        };
        
        wsRef.current.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            
            if (message.type === 'analysis_complete') {
              // 분석 완료 알림
              addNotification({
                type: 'success',
                title: '🎉 분석 완료!',
                message: `대화 분석이 완료되었습니다.`,
                conversationId: message.conversationId,
                link: `/analysis/${message.conversationId}/summary`
              });
              
              // 브라우저 알림도 표시
              if ('Notification' in window && Notification.permission === 'granted') {
                const notification = new Notification('GAON - 분석 완료!', {
                  body: '대화 분석이 완료되었습니다. 클릭해서 결과를 확인하세요.',
                  icon: '/favicon.ico'
                });
                
                notification.onclick = () => {
                  window.focus();
                  router.push(`/analysis/${message.conversationId}/summary`);
                  notification.close();
                };
              }
            }
          } catch (error) {
            console.error('WebSocket 메시지 파싱 오류:', error);
          }
        };
        
        wsRef.current.onclose = () => {
          console.log(`🔌 WebSocket 연결 끊어짐: ${conversationId}`);
        };
        
        wsRef.current.onerror = (error) => {
          console.error('WebSocket 오류:', error);
        };
      } catch (error) {
        console.error('WebSocket 연결 실패:', error);
      }
    };

    // 브라우저 알림 권한 요청
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }

    // WebSocket 연결 시작
    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [conversationId, router, addNotification]);

  return {
    addConnection: globalWsManager.addConnection.bind(globalWsManager),
    removeConnection: globalWsManager.removeConnection.bind(globalWsManager)
  };
}
