import { useEffect, useRef } from 'react'
import { Message } from '../../schemas/realtime'

interface MessageListProps {
  messages: Message[]
  currentUserId: number
}

export const MessageList = ({ messages, currentUserId }: MessageListProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 새 메시지가 올 때마다 스크롤을 맨 아래로
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const isMyMessage = (userId: number) => userId === currentUserId
  const isSystemMessage = (userId: number) => userId === 0

  const getUserColor = (userId: number) => {
    const colors = [
      'bg-blue-100 text-blue-800',      // 파스텔 블루
      'bg-green-100 text-green-800',    // 파스텔 그린
      'bg-purple-100 text-purple-800',  // 파스텔 퍼플
      'bg-pink-100 text-pink-800',      // 파스텔 핑크
      'bg-yellow-100 text-yellow-800',  // 파스텔 옐로우
      'bg-indigo-100 text-indigo-800',  // 파스텔 인디고
    ]
    return colors[userId % colors.length]
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.length === 0 ? (
        <div className="text-center text-gray-500 mt-8">
          아직 메시지가 없습니다. 첫 번째 메시지를 보내보세요!
        </div>
      ) : (
        messages.map((message) => {
          if (isSystemMessage(message.user_id)) {
            return (
              <div key={message.id} className="text-center">
                <span className="inline-block px-3 py-1 bg-gray-200 text-gray-600 text-sm rounded-full">
                  {message.message}
                </span>
              </div>
            )
          }

          const userColor = getUserColor(message.user_id)

          return (
            <div key={message.id} className="flex justify-start">
              <div className="max-w-xs lg:max-w-md">
                <div className="mb-1">
                  <span className="text-xs text-gray-600 font-medium">
                    {message.user_name || `사용자 ${message.user_id}`}
                  </span>
                  <span className="text-xs text-gray-400 ml-2">
                    {formatTime(message.timestamp)}
                  </span>
                </div>
                <div className={`px-4 py-2 rounded-lg ${userColor}`}>
                  <p className="text-sm">{message.message}</p>
                </div>
              </div>
            </div>
          )
        })
      )}
      <div ref={messagesEndRef} />
    </div>
  )
}
