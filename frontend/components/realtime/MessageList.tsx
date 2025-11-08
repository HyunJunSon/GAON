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

          const isMine = isMyMessage(message.user_id)

          return (
            <div
              key={message.id}
              className={`flex ${isMine ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-xs lg:max-w-md ${isMine ? 'order-2' : 'order-1'}`}>
                <div
                  className={`px-4 py-2 rounded-lg ${
                    isMine
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-800'
                  }`}
                >
                  <p className="text-sm">{message.message}</p>
                </div>
                <div className={`text-xs text-gray-500 mt-1 ${isMine ? 'text-right' : 'text-left'}`}>
                  {!isMine && (
                    <span className="mr-2">사용자 {message.user_id}</span>
                  )}
                  {formatTime(message.timestamp)}
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
