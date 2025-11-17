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

export function useGlobalWebSocket() {
  const router = useRouter();
  const { addNotification } = useNotificationStore();
  const hasListenerRef = useRef(false);

  useEffect(() => {
    if (hasListenerRef.current) return;
    hasListenerRef.current = true;

    const handleAnalysisComplete = (event: CustomEvent) => {
      const { conversationId, data } = event.detail;
      
      // NotificationCenter에 알림 추가
      addNotification({
        type: 'success',
        title: '🎉 분석 완료!',
        message: `대화 분석이 완료되었습니다. (점수: ${data.score})`,
        conversationId,
        link: `/analysis/${conversationId}/summary`
      });
    };

    window.addEventListener('gaon-analysis-complete', handleAnalysisComplete as EventListener);

    return () => {
      window.removeEventListener('gaon-analysis-complete', handleAnalysisComplete as EventListener);
      hasListenerRef.current = false;
    };
  }, [router, addNotification]);

  return {
    addConnection: globalWsManager.addConnection.bind(globalWsManager),
    removeConnection: globalWsManager.removeConnection.bind(globalWsManager)
  };
}
