import { useState } from 'react'
import { useRealtimeChat } from '../../hooks/useRealtimeChat'
import { ConnectionStatus } from './ConnectionStatus'
import { MessageList } from './MessageList'
import { MessageInput } from './MessageInput'
import { UserList } from './UserList'

interface ChatRoomProps {
  familyId: number
  userId: number
  onSessionEnd?: () => void
}

export const ChatRoom = ({ familyId, userId, onSessionEnd }: ChatRoomProps) => {
  const [roomName, setRoomName] = useState('가족 대화방')
  
  const {
    session,
    messages,
    users,
    connectionStatus,
    error,
    isLoading,
    createSession,
    sendChatMessage,
    endSession,
    clearError
  } = useRealtimeChat({ familyId, userId })

  const handleEndSession = async () => {
    await endSession()
    onSessionEnd?.()
  }

  const handleAnalyze = async () => {
    if (!session) return
    
    try {
      const response = await fetch(`http://localhost:8000/api/conversations/realtime/sessions/${session.room_id}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (response.ok) {
        const result = await response.json()
        alert(`분석 완료! 메시지 수: ${result.message_count}`)
        // 필요시 분석 결과 페이지로 이동
      } else {
        alert('분석에 실패했습니다.')
      }
    } catch (error) {
      alert('분석 중 오류가 발생했습니다.')
    }
  }

  const handleCreateSession = () => {
    createSession(roomName)
  }

  // 세션이 없으면 생성 버튼 표시
  if (!session) {
    return (
      <div className="flex flex-col items-center justify-center h-96 bg-gray-50 rounded-lg">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">
          실시간 대화 시작하기
        </h2>
        <p className="text-gray-500 mb-6 text-center">
          가족과 실시간으로 대화를 나누고<br />
          대화 내용을 분석해보세요
        </p>
        
        <div className="w-full max-w-sm mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            채팅방 이름
          </label>
          <input
            type="text"
            value={roomName}
            onChange={(e) => setRoomName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="채팅방 이름을 입력하세요"
          />
        </div>
        
        <button
          onClick={handleCreateSession}
          disabled={isLoading || !roomName.trim()}
          className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? '세션 생성 중...' : '대화 시작하기'}
        </button>
        {error && (
          <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-lg">
            {error}
            <button
              onClick={clearError}
              className="ml-2 text-red-500 hover:text-red-700"
            >
              ✕
            </button>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[600px] bg-white rounded-lg border shadow-sm">
      {/* 헤더 */}
      <div className="flex items-center justify-between p-4 border-b bg-gray-50">
        <div className="flex items-center gap-3">
          <h2 className="font-semibold text-gray-800">
            {session.display_name || session.room_id}
          </h2>
          <ConnectionStatus 
            status={connectionStatus} 
          />
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleAnalyze}
            className="px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600 transition-colors"
          >
            대화 분석하기
          </button>
          <button
            onClick={handleEndSession}
            className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
          >
            종료
          </button>
        </div>
      </div>

      {/* 참여자 목록 */}
      <UserList users={users} currentUserId={userId} />

      {/* 에러 메시지 */}
      {error && (
        <div className="mx-4 mt-2 p-3 bg-red-100 text-red-700 rounded-lg text-sm">
          {error}
          <button
            onClick={clearError}
            className="ml-2 text-red-500 hover:text-red-700"
          >
            ✕
          </button>
        </div>
      )}

      {/* 메시지 목록 */}
      <MessageList messages={messages} currentUserId={userId} />

      {/* 메시지 입력 */}
      <MessageInput
        onSend={sendChatMessage}
        disabled={connectionStatus !== 'connected'}
        placeholder={
          connectionStatus === 'connected' 
            ? "메시지를 입력하세요..." 
            : "연결을 기다리는 중..."
        }
      />
    </div>
  )
}
