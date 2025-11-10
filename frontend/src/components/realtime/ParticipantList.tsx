import React from 'react';
import { Participant, VoiceActivity } from '../../types/realtime';

interface ParticipantListProps {
  participants: Participant[];
  voiceActivity: VoiceActivity[];
  currentUserId: string;
}

export const ParticipantList: React.FC<ParticipantListProps> = ({
  participants,
  voiceActivity,
  currentUserId
}) => {
  const getVoiceActivity = (userId: string) => {
    return voiceActivity.find(v => v.user_id === userId);
  };

  return (
    <div className="participant-list">
      <div className="participant-header">
        <h3>참가자 ({participants.length})</h3>
      </div>
      
      <div className="participants">
        {participants.map((participant) => {
          const activity = getVoiceActivity(participant.id);
          const isCurrentUser = participant.id === currentUserId;
          
          return (
            <div
              key={participant.id}
              className={`participant ${isCurrentUser ? 'current-user' : ''} ${
                activity?.is_speaking ? 'speaking' : ''
              }`}
            >
              <div className="participant-avatar">
                <div className="avatar-circle">
                  {participant.name.charAt(0).toUpperCase()}
                </div>
                
                {/* 음성 활동 표시 */}
                {activity?.is_speaking && (
                  <div className="voice-indicator">
                    <div className="voice-waves">
                      <div className="wave"></div>
                      <div className="wave"></div>
                      <div className="wave"></div>
                    </div>
                  </div>
                )}
                
                {/* 음소거 표시 */}
                {participant.is_muted && (
                  <div className="mute-indicator">🔇</div>
                )}
              </div>
              
              <div className="participant-info">
                <div className="participant-name">
                  {participant.name}
                  {isCurrentUser && <span className="you-badge">(나)</span>}
                </div>
                
                <div className="participant-status">
                  {activity?.is_speaking ? (
                    <span className="speaking-text">🎤 말하는 중</span>
                  ) : participant.is_muted ? (
                    <span className="muted-text">🔇 음소거</span>
                  ) : (
                    <span className="idle-text">대기 중</span>
                  )}
                </div>
                
                {/* 음성 레벨 바 */}
                {activity && (
                  <div className="voice-level-bar">
                    <div 
                      className="voice-level-fill"
                      style={{ width: `${activity.volume * 100}%` }}
                    ></div>
                  </div>
                )}
              </div>
              
              <div className="participant-actions">
                <div className="join-time">
                  {new Date(participant.joined_at).toLocaleTimeString('ko-KR', {
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      
      {participants.length === 0 && (
        <div className="no-participants">
          <p>참가자가 없습니다</p>
        </div>
      )}
    </div>
  );
};
