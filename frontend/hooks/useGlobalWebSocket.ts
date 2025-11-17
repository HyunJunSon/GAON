import { useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useGlobalNotification } from './useGlobalNotification';

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

    const wsUrl = `ws://localhost:8000/ws/analysis/${conversationId}`;
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
  const { showNotification } = useGlobalNotification();
  const hasListenerRef = useRef(false);

  useEffect(() => {
    if (hasListenerRef.current) return;
    hasListenerRef.current = true;

    const handleAnalysisComplete = (event: CustomEvent) => {
      const { conversationId, data } = event.detail;
      
      showNotification({
        title: '🎉 분석 완료!',
        body: `대화 분석이 완료되었습니다. (점수: ${data.score})`,
        onClick: () => {
          // 분석 결과 페이지로 이동
          router.push(`/conversations/${conversationId}`);
        }
      });
    };

    window.addEventListener('gaon-analysis-complete', handleAnalysisComplete as EventListener);

    return () => {
      window.removeEventListener('gaon-analysis-complete', handleAnalysisComplete as EventListener);
      hasListenerRef.current = false;
    };
  }, [router, showNotification]);

  return {
    addConnection: globalWsManager.addConnection.bind(globalWsManager),
    removeConnection: globalWsManager.removeConnection.bind(globalWsManager)
  };
}
