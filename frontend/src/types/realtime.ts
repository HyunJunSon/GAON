export interface RealtimeMessage {
  id: string;
  type: 'transcript' | 'message' | 'audio' | 'system';
  content: string;
  user_id: string;
  user_name?: string;
  timestamp: string;
  is_final?: boolean;
  is_interim?: boolean;
}

export interface VoiceActivity {
  user_id: string;
  is_speaking: boolean;
  volume: number;
}

export interface RealtimeSession {
  id: string;
  name: string;
  participants: Participant[];
  status: 'active' | 'ended' | 'paused';
}

export interface Participant {
  id: string;
  name: string;
  avatar?: string;
  is_speaking: boolean;
  is_muted: boolean;
  joined_at: string;
}
