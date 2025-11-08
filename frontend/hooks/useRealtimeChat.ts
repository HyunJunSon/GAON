import { useState, useCallback, useEffect } from 'react'
import { useWebSocket } from './useWebSocket'
import { realtimeApi } from '../apis/realtime'
import { Message, Session, WebSocketMessage, ConnectionStatus } from '../schemas/realtime'

interface UseRealtimeChatProps {
  familyId: number
  userId: number
}

export const useRealtimeChat = ({ familyId, userId }: UseRealtimeChatProps) => {
  const [session, setSession] = useState<Session | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [users, setUsers] = useState<number[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  // WebSocket URL 생성
  const wsUrl = session ? realtimeApi.getWebSocketUrl(session.room_id, userId, familyId) : null

  // WebSocket 이벤트 핸들러
  const handleMessage = useCallback((wsMessage: WebSocketMessage) => {
    switch (wsMessage.type) {
      case 'message':
        const newMessage: Message = {
          id: wsMessage.data.id,
          user_id: wsMessage.data.user_id,
          message: wsMessage.data.message,
          timestamp: wsMessage.data.timestamp,
          message_type: 'text'
        }
        setMessages(prev => [...prev, newMessage])
        break

      case 'user_joined':
        setUsers(wsMessage.data.users || [])
        if (wsMessage.data.message) {
          const systemMessage: Message = {
            id: Date.now(), // 임시 ID
            user_id: 0, // 시스템 메시지
            message: wsMessage.data.message,
            timestamp: new Date().toISOString(),
            message_type: 'system'
          }
          setMessages(prev => [...prev, systemMessage])
        }
        break

      case 'user_left':
        setUsers(wsMessage.data.users || [])
        if (wsMessage.data.message) {
          const systemMessage: Message = {
            id: Date.now(),
            user_id: 0,
            message: wsMessage.data.message,
            timestamp: new Date().toISOString(),
            message_type: 'system'
          }
          setMessages(prev => [...prev, systemMessage])
        }
        break

      case 'session_ended':
        if (wsMessage.data.message) {
          const systemMessage: Message = {
            id: Date.now(),
            user_id: 0,
            message: wsMessage.data.message,
            timestamp: new Date().toISOString(),
            message_type: 'system'
          }
          setMessages(prev => [...prev, systemMessage])
        }
        break

      case 'error':
        setError(wsMessage.data.message || '알 수 없는 오류가 발생했습니다.')
        break
    }
  }, [])

  const handleConnect = useCallback(() => {
    setError(null)
  }, [])

  const handleDisconnect = useCallback(() => {
    // 연결이 끊어졌을 때의 처리
  }, [])

  const handleError = useCallback((error: Event) => {
    setError('WebSocket 연결 오류가 발생했습니다.')
  }, [])

  // WebSocket 훅 사용
  const { connectionStatus, sendMessage } = useWebSocket({
    url: wsUrl,
    onMessage: handleMessage,
    onConnect: handleConnect,
    onDisconnect: handleDisconnect,
    onError: handleError
  })

  // 세션 생성
  const createSession = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const newSession = await realtimeApi.createSession(familyId)
      setSession(newSession)
      setMessages([])
      setUsers([])
    } catch (error) {
      setError('세션 생성에 실패했습니다.')
    } finally {
      setIsLoading(false)
    }
  }, [familyId])

  // 메시지 전송
  const sendChatMessage = useCallback((message: string) => {
    if (!message.trim()) return false

    const success = sendMessage({
      type: 'message',
      content: message.trim()
    })

    if (!success) {
      setError('메시지 전송에 실패했습니다.')
    }

    return success
  }, [sendMessage])

  // 세션 종료
  const endSession = useCallback(async () => {
    if (!session) return

    try {
      // WebSocket으로 종료 신호 전송
      sendMessage({
        type: 'end_session'
      })

      // HTTP API로도 종료 요청
      await realtimeApi.endSession(session.room_id)
      
      setSession(null)
      setMessages([])
      setUsers([])
    } catch (error) {
      setError('세션 종료에 실패했습니다.')
    }
  }, [session, sendMessage])

  // 대화 내보내기
  const exportConversation = useCallback(async () => {
    if (!session) return null

    try {
      return await realtimeApi.exportConversation(session.room_id)
    } catch (error) {
      setError('대화 내보내기에 실패했습니다.')
      return null
    }
  }, [session])

  return {
    // 상태
    session,
    messages,
    users,
    connectionStatus,
    error,
    isLoading,

    // 액션
    createSession,
    sendChatMessage,
    endSession,
    exportConversation,

    // 유틸리티
    clearError: () => setError(null)
  }
}
