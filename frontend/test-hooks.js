// 훅 테스트 스크립트
console.log('🧪 실시간 대화 훅 테스트 시작...')

// 기본적인 함수 존재 여부 확인
function testHookExports() {
  try {
    // TypeScript 파일을 직접 테스트하기 어려우므로 파일 존재 여부만 확인
    const fs = require('fs')
    const path = require('path')
    
    const webSocketHookPath = path.join(__dirname, 'hooks', 'useWebSocket.ts')
    const realtimeChatHookPath = path.join(__dirname, 'hooks', 'useRealtimeChat.ts')
    
    if (fs.existsSync(webSocketHookPath)) {
      console.log('✅ useWebSocket 훅 파일 존재')
    } else {
      console.log('❌ useWebSocket 훅 파일 없음')
      return false
    }
    
    if (fs.existsSync(realtimeChatHookPath)) {
      console.log('✅ useRealtimeChat 훅 파일 존재')
    } else {
      console.log('❌ useRealtimeChat 훅 파일 없음')
      return false
    }
    
    // 파일 내용 기본 검증
    const webSocketContent = fs.readFileSync(webSocketHookPath, 'utf8')
    const realtimeChatContent = fs.readFileSync(realtimeChatHookPath, 'utf8')
    
    if (webSocketContent.includes('useWebSocket') && webSocketContent.includes('WebSocket')) {
      console.log('✅ useWebSocket 훅 기본 구조 확인')
    } else {
      console.log('❌ useWebSocket 훅 구조 문제')
      return false
    }
    
    if (realtimeChatContent.includes('useRealtimeChat') && realtimeChatContent.includes('sendMessage')) {
      console.log('✅ useRealtimeChat 훅 기본 구조 확인')
    } else {
      console.log('❌ useRealtimeChat 훅 구조 문제')
      return false
    }
    
    return true
  } catch (error) {
    console.log('❌ 훅 테스트 실패:', error.message)
    return false
  }
}

// API 함수 테스트
function testApiExports() {
  try {
    const fs = require('fs')
    const path = require('path')
    
    const apiPath = path.join(__dirname, 'apis', 'realtime.ts')
    
    if (!fs.existsSync(apiPath)) {
      console.log('❌ realtime API 파일 없음')
      return false
    }
    
    const apiContent = fs.readFileSync(apiPath, 'utf8')
    
    const requiredFunctions = ['createSession', 'endSession', 'exportConversation', 'getWebSocketUrl']
    
    for (const func of requiredFunctions) {
      if (apiContent.includes(func)) {
        console.log(`✅ ${func} API 함수 존재`)
      } else {
        console.log(`❌ ${func} API 함수 없음`)
        return false
      }
    }
    
    return true
  } catch (error) {
    console.log('❌ API 테스트 실패:', error.message)
    return false
  }
}

// 테스트 실행
function runHookTests() {
  const hookTest = testHookExports()
  const apiTest = testApiExports()
  
  if (hookTest && apiTest) {
    console.log('🎉 모든 훅 테스트 통과!')
    return true
  } else {
    console.log('❌ 일부 테스트 실패')
    return false
  }
}

// 메인 실행
if (require.main === module) {
  const success = runHookTests()
  process.exit(success ? 0 : 1)
}

module.exports = { runHookTests }
