// 컴포넌트 테스트 스크립트
console.log('🧪 실시간 대화 컴포넌트 테스트 시작...')

function testComponentFiles() {
  const fs = require('fs')
  const path = require('path')
  
  const components = [
    'ConnectionStatus.tsx',
    'MessageInput.tsx', 
    'MessageList.tsx',
    'UserList.tsx',
    'ChatRoom.tsx'
  ]
  
  const componentDir = path.join(__dirname, 'components', 'realtime')
  
  try {
    for (const component of components) {
      const componentPath = path.join(componentDir, component)
      
      if (fs.existsSync(componentPath)) {
        console.log(`✅ ${component} 컴포넌트 파일 존재`)
        
        // 기본 구조 검증
        const content = fs.readFileSync(componentPath, 'utf8')
        const componentName = component.replace('.tsx', '')
        
        if (content.includes(`export const ${componentName}`) || content.includes(`export default`)) {
          console.log(`✅ ${componentName} 컴포넌트 export 확인`)
        } else {
          console.log(`❌ ${componentName} 컴포넌트 export 없음`)
          return false
        }
        
        // React 관련 import 확인
        if (content.includes('import') && (content.includes('react') || content.includes('React'))) {
          console.log(`✅ ${componentName} React import 확인`)
        } else if (content.includes('interface') || content.includes('Props')) {
          console.log(`✅ ${componentName} TypeScript 인터페이스 확인`)
        }
        
      } else {
        console.log(`❌ ${component} 컴포넌트 파일 없음`)
        return false
      }
    }
    
    return true
  } catch (error) {
    console.log('❌ 컴포넌트 테스트 실패:', error.message)
    return false
  }
}

function testComponentStructure() {
  const fs = require('fs')
  const path = require('path')
  
  try {
    // ChatRoom 컴포넌트가 다른 컴포넌트들을 import하는지 확인
    const chatRoomPath = path.join(__dirname, 'components', 'realtime', 'ChatRoom.tsx')
    const chatRoomContent = fs.readFileSync(chatRoomPath, 'utf8')
    
    const requiredImports = [
      'ConnectionStatus',
      'MessageList', 
      'MessageInput',
      'UserList',
      'useRealtimeChat'
    ]
    
    for (const importName of requiredImports) {
      if (chatRoomContent.includes(importName)) {
        console.log(`✅ ChatRoom에서 ${importName} import 확인`)
      } else {
        console.log(`❌ ChatRoom에서 ${importName} import 없음`)
        return false
      }
    }
    
    return true
  } catch (error) {
    console.log('❌ 컴포넌트 구조 테스트 실패:', error.message)
    return false
  }
}

// 테스트 실행
function runComponentTests() {
  const fileTest = testComponentFiles()
  const structureTest = testComponentStructure()
  
  if (fileTest && structureTest) {
    console.log('🎉 모든 컴포넌트 테스트 통과!')
    return true
  } else {
    console.log('❌ 일부 컴포넌트 테스트 실패')
    return false
  }
}

// 메인 실행
if (require.main === module) {
  const success = runComponentTests()
  process.exit(success ? 0 : 1)
}

module.exports = { runComponentTests }
