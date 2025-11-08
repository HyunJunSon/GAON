// 간단한 테스트 스크립트
const { z } = require('zod')

// 스키마 정의 (TypeScript 파일에서 복사)
const MessageSchema = z.object({
  id: z.number(),
  user_id: z.number(),
  message: z.string(),
  timestamp: z.string(),
  message_type: z.enum(['text', 'system'])
})

const SessionSchema = z.object({
  id: z.number(),
  room_id: z.string(),
  family_id: z.number(),
  created_at: z.string(),
  ended_at: z.string().nullable(),
  status: z.enum(['active', 'ended'])
})

// 테스트 함수
function runTests() {
  console.log('🧪 실시간 대화 스키마 테스트 시작...')
  
  // Message 스키마 테스트
  const validMessage = {
    id: 1,
    user_id: 1,
    message: '안녕하세요!',
    timestamp: '2023-01-01T12:00:00Z',
    message_type: 'text'
  }
  
  try {
    MessageSchema.parse(validMessage)
    console.log('✅ Message 스키마 검증 성공')
  } catch (error) {
    console.log('❌ Message 스키마 검증 실패:', error.message)
    return false
  }
  
  // Session 스키마 테스트
  const validSession = {
    id: 1,
    room_id: 'room_12345678',
    family_id: 1,
    created_at: '2023-01-01T12:00:00Z',
    ended_at: null,
    status: 'active'
  }
  
  try {
    SessionSchema.parse(validSession)
    console.log('✅ Session 스키마 검증 성공')
  } catch (error) {
    console.log('❌ Session 스키마 검증 실패:', error.message)
    return false
  }
  
  // 잘못된 데이터 테스트
  const invalidMessage = {
    id: 'invalid',
    user_id: 1,
    message: '안녕하세요!',
    timestamp: '2023-01-01T12:00:00Z',
    message_type: 'text'
  }
  
  try {
    MessageSchema.parse(invalidMessage)
    console.log('❌ 잘못된 Message 데이터가 통과됨')
    return false
  } catch (error) {
    console.log('✅ 잘못된 Message 데이터 올바르게 거부됨')
  }
  
  console.log('🎉 모든 테스트 통과!')
  return true
}

// 테스트 실행
if (require.main === module) {
  const success = runTests()
  process.exit(success ? 0 : 1)
}

module.exports = { runTests }
