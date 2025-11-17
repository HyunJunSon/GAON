import { useEffect, useRef, useState } from 'react';
import { useGlobalWebSocket } from './useGlobalWebSocket';

interface WebSocketMessage {
  type: 'analysis_progress' | 'analysis_complete' | 'analysis_failed';
  conversationId: string;
  data: any;
}

interface UseWebSocketProps {
  conversationId: string;
  onAnalysisComplete?: (data: any) => void;
  onAnalysisProgress?: (data: any) => void;
  onAnalysisError?: (error: string) => void;
  enableGlobalNotification?: boolean; // 전역 알림 사용 여부
}

export function useWebSocket({
  conversationId,
  onAnalysisComplete,
  onAnalysisProgress,
  onAnalysisError,
  enableGlobalNotification = true
}: UseWebSocketProps) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const { addConnection, removeConnection } = useGlobalWebSocket();

  useEffect(() => {
    if (!conversationId) return;

    // 전역 알림이 활성화된 경우 전역 WebSocket 연결 추가
    if (enableGlobalNotification) {
      addConnection(conversationId);
    }

    // 페이지별 WebSocket 연결 (실시간 진행률 등을 위해)
    const wsUrl = `ws://localhost:8000/ws/analysis/${conversationId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('페이지 WebSocket 연결됨:', conversationId);
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        
        switch (message.type) {
          case 'analysis_complete':
            console.log('분석 완료:', message.data);
            onAnalysisComplete?.(message.data);
            break;
          case 'analysis_progress':
            console.log('분석 진행률:', message.data);
            onAnalysisProgress?.(message.data);
            break;
          case 'analysis_failed':
            console.log('분석 실패:', message.data);
            onAnalysisError?.(message.data.error);
            break;
        }
      } catch (error) {
        console.error('WebSocket 메시지 파싱 오류:', error);
      }
    };

    ws.onclose = () => {
      console.log('페이지 WebSocket 연결 종료');
      setIsConnected(false);
    };

    ws.onerror = (error) => {
      console.error('WebSocket 오류:', error);
      setIsConnected(false);
    };

    // Keep-alive ping
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
      ws.close();
      
      // 컴포넌트 언마운트 시 전역 연결은 유지 (다른 페이지에서도 알림 받기 위해)
      // removeConnection(conversationId); // 주석 처리
    };
  }, [conversationId, onAnalysisComplete, onAnalysisProgress, onAnalysisError, enableGlobalNotification, addConnection]);

  return { isConnected };
}
