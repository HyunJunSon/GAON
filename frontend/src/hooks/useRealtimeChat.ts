import { useState, useEffect, useCallback, useRef } from 'react';
import { RealtimeMessage, VoiceActivity, Participant } from '../types/realtime';

export const useRealtimeChat = (sessionId: string, userId: string) => {
  const [messages, setMessages] = useState<RealtimeMessage[]>([]);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [voiceActivity, setVoiceActivity] = useState<VoiceActivity[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttempts = useRef(0);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setConnectionStatus('connecting');
    const ws = new WebSocket(`ws://localhost:8000/realtime/ws/${sessionId}`);
    
    ws.onopen = () => {
      setIsConnected(true);
      setConnectionStatus('connected');
      reconnectAttempts.current = 0;
      console.log('🔗 WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const message: RealtimeMessage = JSON.parse(event.data);
        
        if (message.type === 'transcript') {
          setMessages(prev => {
            // 임시 메시지 업데이트 또는 새 메시지 추가
            if (message.is_interim) {
              const existingIndex = prev.findIndex(m => 
                m.user_id === message.user_id && m.is_interim
              );
              if (existingIndex >= 0) {
                const updated = [...prev];
                updated[existingIndex] = { ...message, id: `interim-${Date.now()}` };
                return updated;
              }
            }
            return [...prev, { ...message, id: `msg-${Date.now()}` }];
          });
        } else if (message.type === 'voice_activity') {
          setVoiceActivity(prev => {
            const updated = prev.filter(v => v.user_id !== message.user_id);
            return [...updated, {
              user_id: message.user_id,
              is_speaking: message.content === 'speaking',
              volume: parseFloat(message.content) || 0
            }];
          });
        }
      } catch (error) {
        console.error('Failed to parse message:', error);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      setConnectionStatus('disconnected');
      
      // 자동 재연결
      if (reconnectAttempts.current < 5) {
        reconnectAttempts.current++;
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log(`🔄 Reconnecting... (${reconnectAttempts.current}/5)`);
          connect();
        }, Math.pow(2, reconnectAttempts.current) * 1000);
      }
    };

    ws.onerror = () => {
      setConnectionStatus('error');
    };

    wsRef.current = ws;
  }, [sessionId]);

  const sendMessage = useCallback((message: Partial<RealtimeMessage>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        ...message,
        user_id: userId,
        timestamp: new Date().toISOString()
      }));
    }
  }, [userId]);

  const sendAudio = useCallback((audioBlob: Blob, isInterim = false) => {
    const reader = new FileReader();
    reader.onload = () => {
      const base64Audio = (reader.result as string).split(',')[1];
      sendMessage({
        type: 'audio',
        audio: base64Audio,
        is_final: !isInterim
      });
    };
    reader.readAsDataURL(audioBlob);
  }, [sendMessage]);

  useEffect(() => {
    connect();
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsRef.current?.close();
    };
  }, [connect]);

  return {
    messages,
    participants,
    voiceActivity,
    isConnected,
    connectionStatus,
    sendMessage,
    sendAudio,
    reconnect: connect
  };
};
