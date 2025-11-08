// 통합 테스트 스크립트
console.log('🧪 실시간 대화 통합 테스트 시작...')

function testPageIntegration() {
  const fs = require('fs')
  const path = require('path')
  
  try {
    // 대화 페이지 파일 확인
    const conversationPagePath = path.join(__dirname, 'app', 'conversation', 'page.tsx')
    
    if (!fs.existsSync(conversationPagePath)) {
      console.log('❌ 대화 페이지 파일 없음')
      return false
    }
    
    const pageContent = fs.readFileSync(conversationPagePath, 'utf8')
    
    // 필수 요소들 확인
    const requiredElements = [
      'ChatRoom',
      'activeTab',
      'realtime',
      'upload',
      'TabType'
    ]
    
    for (const element of requiredElements) {
      if (pageContent.includes(element)) {
        console.log(`✅ 대화 페이지에서 ${element} 확인`)
      } else {
        console.log(`❌ 대화 페이지에서 ${element} 없음`)
        return false
      }
    }
    
    // 탭 구조 확인
    if (pageContent.includes('파일 업로드') && pageContent.includes('실시간 대화')) {
      console.log('✅ 탭 구조 확인')
    } else {
      console.log('❌ 탭 구조 없음')
      return false
    }
    
    return true
  } catch (error) {
    console.log('❌ 페이지 통합 테스트 실패:', error.message)
    return false
  }
}

function testAllComponents() {
  const fs = require('fs')
  const path = require('path')
  
  try {
    // 모든 필수 파일들이 존재하는지 확인
    const requiredFiles = [
      'schemas/realtime.ts',
      'apis/realtime.ts',
      'hooks/useWebSocket.ts',
      'hooks/useRealtimeChat.ts',
      'components/realtime/ChatRoom.tsx',
      'components/realtime/ConnectionStatus.tsx',
      'components/realtime/MessageInput.tsx',
      'components/realtime/MessageList.tsx',
      'components/realtime/UserList.tsx'
    ]
    
    for (const filePath of requiredFiles) {
      const fullPath = path.join(__dirname, filePath)
      if (fs.existsSync(fullPath)) {
        console.log(`✅ ${filePath} 파일 존재`)
      } else {
        console.log(`❌ ${filePath} 파일 없음`)
        return false
      }
    }
    
    return true
  } catch (error) {
    console.log('❌ 컴포넌트 존재 테스트 실패:', error.message)
    return false
  }
}

function testPackageJson() {
  const fs = require('fs')
  const path = require('path')
  
  try {
    const packagePath = path.join(__dirname, 'package.json')
    const packageContent = JSON.parse(fs.readFileSync(packagePath, 'utf8'))
    
    if (packageContent.dependencies && packageContent.dependencies['socket.io-client']) {
      console.log('✅ socket.io-client 의존성 확인')
      return true
    } else {
      console.log('❌ socket.io-client 의존성 없음')
      return false
    }
  } catch (error) {
    console.log('❌ package.json 테스트 실패:', error.message)
    return false
  }
}

// 전체 테스트 실행
function runIntegrationTests() {
  console.log('\n📋 통합 테스트 체크리스트:')
  
  const tests = [
    { name: '패키지 의존성', fn: testPackageJson },
    { name: '필수 파일 존재', fn: testAllComponents },
    { name: '페이지 통합', fn: testPageIntegration }
  ]
  
  let allPassed = true
  
  for (const test of tests) {
    console.log(`\n🔍 ${test.name} 테스트 중...`)
    const result = test.fn()
    if (!result) {
      allPassed = false
    }
  }
  
  console.log('\n' + '='.repeat(50))
  if (allPassed) {
    console.log('🎉 모든 통합 테스트 통과!')
    console.log('✨ 실시간 대화 기능이 성공적으로 통합되었습니다!')
  } else {
    console.log('❌ 일부 통합 테스트 실패')
  }
  
  return allPassed
}

// 메인 실행
if (require.main === module) {
  const success = runIntegrationTests()
  process.exit(success ? 0 : 1)
}

module.exports = { runIntegrationTests }
