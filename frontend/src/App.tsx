import React, { useState } from 'react';
import { RealtimeChat } from './components/realtime/RealtimeChat';
import './App.css';

function App() {
  const [sessionId, setSessionId] = useState('demo-session');
  const [userId] = useState(`user-${Math.random().toString(36).substr(2, 9)}`);
  const [userName] = useState(`사용자${Math.floor(Math.random() * 100)}`);
  const [isInSession, setIsInSession] = useState(false);

  const joinSession = () => {
    setIsInSession(true);
  };

  const leaveSession = () => {
    setIsInSession(false);
  };

  if (isInSession) {
    return (
      <div className="app">
        <RealtimeChat
          sessionId={sessionId}
          userId={userId}
          userName={userName}
        />
        <button 
          className="leave-button"
          onClick={leaveSession}
        >
          세션 나가기
        </button>
      </div>
    );
  }

  return (
    <div className="app">
      <div className="welcome-screen">
        <div className="welcome-card">
          <h1>🎤 GAON 실시간 음성 대화</h1>
          <p>실시간으로 음성을 텍스트로 변환하여 대화하세요</p>
          
          <div className="session-form">
            <label>
              세션 ID:
              <input
                type="text"
                value={sessionId}
                onChange={(e) => setSessionId(e.target.value)}
                placeholder="세션 ID를 입력하세요"
              />
            </label>
            
            <button 
              className="join-button"
              onClick={joinSession}
              disabled={!sessionId.trim()}
            >
              세션 참가하기
            </button>
          </div>
          
          <div className="features">
            <div className="feature">
              <span className="feature-icon">🎤</span>
              <span>실시간 음성 인식</span>
            </div>
            <div className="feature">
              <span className="feature-icon">💬</span>
              <span>즉시 텍스트 변환</span>
            </div>
            <div className="feature">
              <span className="feature-icon">👥</span>
              <span>다중 사용자 지원</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
