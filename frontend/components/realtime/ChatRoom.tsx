import { useState, useEffect } from 'react'
import { useWebSocket } from '../../hooks/useWebSocket'
import { apiFetch } from '@/apis/client'

interface ChatRoomProps {
  sessionId: number;
  familyId: number
  userId: number
  onSessionEnd?: () => void
}

interface Message {
  id: number;
  user_id: number;
  user_name: string;
  message: string;
  timestamp: string;
}

export const ChatRoom = ({ sessionId, familyId, userId, onSessionEnd }: ChatRoomProps) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [roomId, setRoomId] = useState<string>('');
  const [inputMessage, setInputMessage] = useState('');

  console.log('ChatRoom props:', { sessionId, familyId, userId });

  // 세션 정보 가져오기
  useEffect(() => {
    const fetchSession = async () => {
      try {
        const data = await apiFetch<{sessions: any[]}>(`/api/conversations/realtime/sessions/family/${familyId}`);
        const session = data.sessions?.find((s: any) => s.id === sessionId);
        if (session) {
          setRoomId(session.room_id);
          console.log('세션 찾음:', session);
        }
      } catch (error) {
        console.error('세션 정보 조회 실패:', error);
      }
    };
    fetchSession();
  }, [sessionId, familyId]);

  // WebSocket URL
  const wsUrl = roomId ? `ws://localhost:8000/api/conversations/realtime/ws/${roomId}?user_id=${userId}&family_id=${familyId}` : null;

  console.log('WebSocket URL:', wsUrl);

  const { connectionStatus, sendMessage } = useWebSocket({
    url: wsUrl,
    onMessage: (wsMessage: any) => {
      console.log('WebSocket 메시지 수신:', wsMessage);
      if (wsMessage.type === 'message') {
        setMessages(prev => [...prev, {
          id: wsMessage.data.id,
          user_id: wsMessage.data.user_id,
          user_name: wsMessage.data.user_name,
          message: wsMessage.data.message,
          timestamp: wsMessage.data.timestamp
        }]);
      } else if (wsMessage.type === 'user_joined' || wsMessage.type === 'user_left') {
        setUsers(wsMessage.data.users || []);
      }
    },
    onConnect: () => console.log('WebSocket 연결됨'),
    onDisconnect: () => console.log('WebSocket 연결 해제'),
    onError: (error) => console.error('WebSocket 오류:', error)
  });

  const handleSendMessage = () => {
    if (inputMessage.trim() && sendMessage) {
      sendMessage({
        type: 'message',
        content: inputMessage.trim()
      });
      setInputMessage('');
    }
  };

  return (
    <div className="flex flex-col h-96 border rounded-lg">
      <div className="p-4 border-b">
        <h3 className="font-medium">채팅방 (연결상태: {connectionStatus})</h3>
        <p className="text-sm text-gray-600">참여자: {users.length}명</p>
      </div>
      
      <div className="flex-1 p-4 overflow-y-auto">
        {messages.map((msg) => (
          <div key={msg.id} className="mb-2">
            <span className="font-medium">{msg.user_name}: </span>
            <span>{msg.message}</span>
          </div>
        ))}
      </div>
      
      <div className="p-4 border-t flex gap-2">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          className="flex-1 px-3 py-2 border rounded"
          placeholder="메시지를 입력하세요..."
        />
        <button
          onClick={handleSendMessage}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          전송
        </button>
      </div>
    </div>
  );
}
