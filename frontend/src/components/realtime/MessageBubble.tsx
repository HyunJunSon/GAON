import React from 'react';
import { RealtimeMessage } from '../../types/realtime';

interface MessageBubbleProps {
  message: RealtimeMessage;
  isOwn: boolean;
  userName: string;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  isOwn,
  userName
}) => {
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getMessageIcon = () => {
    switch (message.type) {
      case 'transcript':
        return '🎤';
      case 'message':
        return '💬';
      case 'system':
        return '🔔';
      default:
        return '';
    }
  };

  return (
    <div className={`message-bubble ${isOwn ? 'own' : 'other'} ${message.type}`}>
      {!isOwn && (
        <div className="message-avatar">
          <div className="avatar-circle">
            {userName.charAt(0).toUpperCase()}
          </div>
        </div>
      )}
      
      <div className="message-content">
        {!isOwn && (
          <div className="message-header">
            <span className="user-name">{userName}</span>
            <span className="message-type">{getMessageIcon()}</span>
          </div>
        )}
        
        <div className={`message-text ${message.is_interim ? 'interim' : ''}`}>
          {message.content}
          {message.is_interim && (
            <span className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </span>
          )}
        </div>
        
        <div className="message-footer">
          <span className="timestamp">{formatTime(message.timestamp)}</span>
          {message.type === 'transcript' && (
            <span className="transcript-badge">음성변환</span>
          )}
          {isOwn && (
            <span className="message-status">✓</span>
          )}
        </div>
      </div>
    </div>
  );
};
