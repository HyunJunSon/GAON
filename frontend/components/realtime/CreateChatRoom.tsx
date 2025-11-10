'use client';

import { useState } from 'react';
import { apiFetch } from '@/apis/client';

interface CreateChatRoomProps {
  familyId: number;
  userId: number;
  onRoomCreated: (sessionId: number) => void;
  onCancel: () => void;
}

export function CreateChatRoom({ familyId, userId, onRoomCreated, onCancel }: CreateChatRoomProps) {
  const [roomName, setRoomName] = useState('');
  const [creating, setCreating] = useState(false);

  const handleCreate = async () => {
    if (!roomName.trim()) return;

    setCreating(true);
    try {
      const params = new URLSearchParams({
        family_id: String(familyId),
        room_name: roomName.trim(),
      });

      const data = await apiFetch(`/api/conversations/realtime/sessions?${params}`, {
        method: 'POST',
      });

      console.log('채팅방 생성 성공:', data);
      onRoomCreated(data.id);
    } catch (error) {
      console.error('채팅방 생성 실패:', error);
      alert(`채팅방 생성 실패: ${error instanceof Error ? error.message : '알 수 없는 오류'}`);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="border rounded-lg p-6 bg-white shadow-sm">
      <h3 className="text-lg font-medium mb-4">새 채팅방 만들기</h3>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            채팅방 이름
          </label>
          <input
            type="text"
            value={roomName}
            onChange={(e) => setRoomName(e.target.value)}
            placeholder="예: 가족 대화방, 주말 계획 등"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            maxLength={50}
          />
        </div>

        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            취소
          </button>
          <button
            onClick={handleCreate}
            disabled={!roomName.trim() || creating}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {creating ? '생성 중...' : '채팅방 만들기'}
          </button>
        </div>
      </div>
    </div>
  );
}
