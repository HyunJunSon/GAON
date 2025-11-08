const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface CreateSessionRequest {
  family_id: number
}

export interface CreateSessionResponse {
  id: number
  room_id: string
  family_id: number
  created_at: string
  ended_at: string | null
  status: 'active' | 'ended'
}

export interface ExportConversationResponse {
  session_id: number
  room_id: string
  conversation_text: string
  message_count: number
}

export const realtimeApi = {
  // 세션 생성
  createSession: async (familyId: number): Promise<CreateSessionResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/conversations/realtime/sessions?family_id=${familyId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (!response.ok) {
      throw new Error('Failed to create session')
    }
    
    return response.json()
  },

  // 세션 종료
  endSession: async (roomId: string): Promise<{ message: string; session_id: number }> => {
    const response = await fetch(`${API_BASE_URL}/api/conversations/realtime/sessions/${roomId}/end`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (!response.ok) {
      throw new Error('Failed to end session')
    }
    
    return response.json()
  },

  // 대화 내보내기
  exportConversation: async (roomId: string): Promise<ExportConversationResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/conversations/realtime/sessions/${roomId}/export`)
    
    if (!response.ok) {
      throw new Error('Failed to export conversation')
    }
    
    return response.json()
  },

  // WebSocket URL 생성
  getWebSocketUrl: (roomId: string, userId: number, familyId: number): string => {
    const wsUrl = API_BASE_URL.replace('http', 'ws')
    return `${wsUrl}/api/conversations/realtime/ws/${roomId}?user_id=${userId}&family_id=${familyId}`
  }
}
