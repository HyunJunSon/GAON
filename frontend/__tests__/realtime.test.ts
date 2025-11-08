import { describe, it, expect } from '@jest/globals'
import { MessageSchema, SessionSchema, WebSocketMessageSchema, SessionStatus, MessageType } from '../schemas/realtime'

describe('Realtime Schemas', () => {
  describe('MessageSchema', () => {
    it('should validate correct message data', () => {
      const validMessage = {
        id: 1,
        user_id: 1,
        message: '안녕하세요!',
        timestamp: '2023-01-01T12:00:00Z',
        message_type: 'text' as const
      }

      const result = MessageSchema.safeParse(validMessage)
      expect(result.success).toBe(true)
    })

    it('should reject invalid message data', () => {
      const invalidMessage = {
        id: 'invalid',
        user_id: 1,
        message: '안녕하세요!',
        timestamp: '2023-01-01T12:00:00Z',
        message_type: 'text'
      }

      const result = MessageSchema.safeParse(invalidMessage)
      expect(result.success).toBe(false)
    })
  })

  describe('SessionSchema', () => {
    it('should validate correct session data', () => {
      const validSession = {
        id: 1,
        room_id: 'room_12345678',
        family_id: 1,
        created_at: '2023-01-01T12:00:00Z',
        ended_at: null,
        status: 'active' as const
      }

      const result = SessionSchema.safeParse(validSession)
      expect(result.success).toBe(true)
    })
  })

  describe('Constants', () => {
    it('should have correct SessionStatus values', () => {
      expect(SessionStatus.ACTIVE).toBe('active')
      expect(SessionStatus.ENDED).toBe('ended')
    })

    it('should have correct MessageType values', () => {
      expect(MessageType.TEXT).toBe('text')
      expect(MessageType.SYSTEM).toBe('system')
    })
  })
})
