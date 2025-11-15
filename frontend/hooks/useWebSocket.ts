'use client';

import { useEffect, useRef, useState } from 'react';

type WebSocketMessage = {
  type: 'analysis_progress' | 'analysis_complete' | 'analysis_failed';
  conversationId: string;
  data: any;
};

type UseWebSocketProps = {
  url: string;
  onMessage?: (message: WebSocketMessage) => void;
  enabled?: boolean;
};

export function useWebSocket({ url, onMessage, enabled = true }: UseWebSocketProps) {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = () => {
    if (!enabled) return;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setError(null);
        console.log('WebSocket 연결됨');
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          onMessage?.(message);
        } catch (err) {
          console.error('WebSocket 메시지 파싱 실패:', err);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        console.log('WebSocket 연결 종료');
        
        // 자동 재연결 (5초 후)
        if (enabled) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, 5000);
        }
      };

      ws.onerror = (error) => {
        setError('WebSocket 연결 오류');
        console.error('WebSocket 오류:', error);
      };

    } catch (err) {
      setError('WebSocket 연결 실패');
      console.error('WebSocket 연결 실패:', err);
    }
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
  };

  const sendMessage = (message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  };

  useEffect(() => {
    if (enabled) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, url]);

  return {
    isConnected,
    error,
    sendMessage,
    disconnect
  };
}
