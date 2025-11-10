import React from 'react';

interface ConnectionStatusProps {
  status: 'connecting' | 'connected' | 'disconnected' | 'error';
  onReconnect: () => void;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  status,
  onReconnect
}) => {
  const getStatusInfo = () => {
    switch (status) {
      case 'connected':
        return {
          icon: '🟢',
          text: '연결됨',
          className: 'connected'
        };
      case 'connecting':
        return {
          icon: '🟡',
          text: '연결 중...',
          className: 'connecting'
        };
      case 'disconnected':
        return {
          icon: '🔴',
          text: '연결 끊김',
          className: 'disconnected'
        };
      case 'error':
        return {
          icon: '⚠️',
          text: '연결 오류',
          className: 'error'
        };
      default:
        return {
          icon: '⚪',
          text: '알 수 없음',
          className: 'unknown'
        };
    }
  };

  const statusInfo = getStatusInfo();

  return (
    <div className={`connection-status ${statusInfo.className}`}>
      <div className="status-indicator">
        <span className="status-icon">{statusInfo.icon}</span>
        <span className="status-text">{statusInfo.text}</span>
      </div>
      
      {(status === 'disconnected' || status === 'error') && (
        <button 
          className="reconnect-button"
          onClick={onReconnect}
        >
          🔄 재연결
        </button>
      )}
      
      {status === 'connecting' && (
        <div className="connecting-animation">
          <div className="dot"></div>
          <div className="dot"></div>
          <div className="dot"></div>
        </div>
      )}
    </div>
  );
};
