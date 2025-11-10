import React, { useState, useEffect, useRef } from 'react';
import { useRealtimeChat } from '../../hooks/useRealtimeChat';
import { useVoiceRecording } from '../../hooks/useVoiceRecording';
import { VoiceVisualizer } from './VoiceVisualizer';
import { MessageBubble } from './MessageBubble';
import { ParticipantList } from './ParticipantList';
import { ConnectionStatus } from './ConnectionStatus';
import './RealtimeChat.css';

interface RealtimeChatProps {
  sessionId: string;
  userId: string;
  userName: string;
}

export const RealtimeChat: React.FC<RealtimeChatProps> = ({
  sessionId,
  userId,
  userName
}) => {
  const [isMuted, setIsMuted] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const {
    messages,
    participants,
    voiceActivity,
    isConnected,
    connectionStatus,
    sendMessage,
    sendAudio,
    reconnect
  } = useRealtimeChat(sessionId, userId);

  const {
    isRecording,
    audioLevel,
    error: recordingError,
    toggleRecording
  } = useVoiceRecording((audioBlob, isInterim) => {
    if (!isMuted) {
      sendAudio(audioBlob, isInterim);
    }
  });

  // 자동 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const currentSpeaker = voiceActivity.find(v => v.is_speaking);

  return (
    <div className="realtime-chat">
      {/* 헤더 */}
      <div className="chat-header">
        <div className="session-info">
          <h2>실시간 대화</h2>
          <span className="session-id">세션: {sessionId}</span>
        </div>
        <ConnectionStatus status={connectionStatus} onReconnect={reconnect} />
      </div>

      <div className="chat-body">
        {/* 참가자 목록 */}
        <div className="participants-sidebar">
          <ParticipantList 
            participants={participants}
            voiceActivity={voiceActivity}
            currentUserId={userId}
          />
        </div>

        {/* 메시지 영역 */}
        <div className="messages-container">
          <div className="messages-list">
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                isOwn={message.user_id === userId}
                userName={message.user_name || `사용자 ${message.user_id.slice(0, 8)}`}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* 현재 말하는 사람 표시 */}
          {currentSpeaker && currentSpeaker.user_id !== userId && (
            <div className="speaking-indicator">
              <div className="speaking-animation">
                <div className="wave"></div>
                <div className="wave"></div>
                <div className="wave"></div>
              </div>
              <span>누군가 말하고 있습니다...</span>
            </div>
          )}
        </div>
      </div>

      {/* 컨트롤 패널 */}
      <div className="chat-controls">
        <div className="voice-controls">
          {/* 음성 시각화 */}
          <VoiceVisualizer 
            audioLevel={audioLevel}
            isRecording={isRecording}
            isActive={currentSpeaker?.user_id === userId}
          />

          {/* 녹음 버튼 */}
          <button
            className={`record-button ${isRecording ? 'recording' : ''} ${isMuted ? 'muted' : ''}`}
            onClick={toggleRecording}
            disabled={!isConnected}
          >
            <div className="record-icon">
              {isRecording ? '⏹️' : '🎤'}
            </div>
            <span>{isRecording ? '녹음 중지' : '음성 입력'}</span>
          </button>

          {/* 음소거 버튼 */}
          <button
            className={`mute-button ${isMuted ? 'muted' : ''}`}
            onClick={() => setIsMuted(!isMuted)}
          >
            {isMuted ? '🔇' : '🔊'}
          </button>
        </div>

        {/* 에러 표시 */}
        {recordingError && (
          <div className="error-message">
            ⚠️ {recordingError}
          </div>
        )}

        {/* 연결 상태 */}
        <div className="connection-info">
          <span className={`status-dot ${connectionStatus}`}></span>
          <span className="status-text">
            {connectionStatus === 'connected' ? '연결됨' : 
             connectionStatus === 'connecting' ? '연결 중...' : 
             connectionStatus === 'error' ? '연결 오류' : '연결 끊김'}
          </span>
        </div>
      </div>
    </div>
  );
};
