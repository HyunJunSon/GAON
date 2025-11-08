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
    exportConversation,
    clearError
  } = useRealtimeChat({ familyId, userId })

  const handleEndSession = async () => {
    await endSession()
    onSessionEnd?.()
  }

  const handleExport = async () => {
    const result = await exportConversation()
    if (result) {
      // 내보내기 성공 시 처리 (예: 다운로드, 분석 페이지로 이동 등)
      console.log('대화 내보내기 완료:', result)
    }
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
        <button
          onClick={createSession}
          disabled={isLoading}
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
    <div className="flex flex-col h-96 bg-white rounded-lg border shadow-sm">
      {/* 헤더 */}
      <div className="flex items-center justify-between p-4 border-b bg-gray-50">
        <div className="flex items-center gap-3">
          <h2 className="font-semibold text-gray-800">
            실시간 대화 - {session.room_id}
          </h2>
          <ConnectionStatus 
            status={connectionStatus} 
          />
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleExport}
            className="px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600 transition-colors"
          >
            내보내기
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
