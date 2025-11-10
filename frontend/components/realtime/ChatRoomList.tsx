'use client';

import { useState, useEffect } from 'react';
import { apiFetch } from '@/apis/client';

interface ChatRoomListProps {
  familyId: number;
  userId: number;
  onJoinRoom: (sessionId: number) => void;
  onCreateRoom: () => void;
  refreshTrigger?: number; // 새로고침 트리거
}

interface ChatSession {
  id: number;
  display_name: string;
  participant_count: number;
  created_at: string;
  status: string;
}

export function ChatRoomList({ familyId, userId, onJoinRoom, onCreateRoom, refreshTrigger }: ChatRoomListProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchActiveSessions();
    
    // 5초마다 채팅방 목록 새로고침
    const interval = setInterval(fetchActiveSessions, 5000);
    
    return () => clearInterval(interval);
  }, [familyId]);

  // refreshTrigger 변경 시 즉시 새로고침
  useEffect(() => {
    if (refreshTrigger) {
      fetchActiveSessions();
    }
  }, [refreshTrigger]);

  const fetchActiveSessions = async () => {
    try {
      console.log('채팅방 목록 조회 시작, familyId:', familyId);
      const data = await apiFetch<{sessions: ChatSession[]}>(`/api/conversations/realtime/sessions/family/${familyId}`);
      console.log('채팅방 목록 데이터:', data);
      setSessions(data.sessions || []);
    } catch (error) {
      console.error('채팅방 목록 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8">채팅방 목록을 불러오는 중...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">채팅방 목록</h3>
        <button
          onClick={onCreateRoom}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          새 채팅방 만들기
        </button>
      </div>

      {sessions.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p>활성화된 채팅방이 없습니다.</p>
          <p className="text-sm mt-2">새 채팅방을 만들어 가족과 대화를 시작해보세요!</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {sessions.map((session) => (
            <div
              key={session.id}
              className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
              onClick={() => onJoinRoom(session.id)}
            >
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-medium">{session.display_name}</h4>
                  <p className="text-sm text-gray-600">
                    참여자 {session.participant_count}명
                  </p>
                </div>
                <div className="text-right">
                  <span className={`inline-block w-2 h-2 rounded-full ${
                    session.status === 'active' ? 'bg-green-500' : 'bg-gray-400'
                  }`} />
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(session.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
