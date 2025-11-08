import { z } from 'zod'

// Enums
export const SessionStatus = {
  ACTIVE: 'active',
  ENDED: 'ended'
} as const

export const MessageType = {
  TEXT: 'text',
  SYSTEM: 'system'
} as const

// Zod Schemas
export const MessageSchema = z.object({
  id: z.number(),
  user_id: z.number(),
  user_name: z.string().optional(),
  message: z.string(),
  timestamp: z.string(),
  message_type: z.enum(['text', 'system'])
})

export const SessionSchema = z.object({
  id: z.number(),
  room_id: z.string(),
  family_id: z.number(),
  display_name: z.string().optional(),
  created_at: z.string(),
  ended_at: z.string().nullable(),
  status: z.enum(['active', 'ended'])
})

export const WebSocketMessageSchema = z.object({
  type: z.string(),
  data: z.record(z.any())
})

// Types
export type Message = z.infer<typeof MessageSchema>
export type Session = z.infer<typeof SessionSchema>
export type WebSocketMessage = z.infer<typeof WebSocketMessageSchema>

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

export interface RealtimeState {
  messages: Message[]
  users: number[]
  connectionStatus: ConnectionStatus
  currentSession: Session | null
  error: string | null
}
