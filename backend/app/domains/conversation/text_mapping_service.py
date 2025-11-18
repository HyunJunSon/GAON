from typing import Dict, List, Optional, Tuple
import re
from datetime import datetime


class TextMappingService:
    """텍스트 파일에 화자 매핑 적용"""
    
    def apply_speaker_mapping_to_text(self, content: str, user_id: int) -> Tuple[str, Dict, bool]:
        """
        텍스트에 화자 매핑을 적용하여 Agent 형식으로 변환
        
        Args:
            content: 원본 텍스트 내용
            user_id: 업로더 사용자 ID (매핑용, 자동 할당하지 않음)
            
        Returns:
            tuple: (변환된 content, speaker_mapping 정보, 분석 가능 여부)
        """
        # 1. 대화 형식 감지 및 파싱
        dialogue_data = self._parse_text_to_dialogue(content)
        
        # 2. 화자 수 확인
        unique_speakers = set(item['speaker_name'] for item in dialogue_data)
        if len(unique_speakers) < 2:
            return "", {}, False  # 분석 불가
        
        # 3. 화자 매핑 생성 (사용자 선택 대기)
        speaker_mapping = self._create_speaker_mapping(dialogue_data)
        
        # 4. Agent 형식으로 변환
        formatted_content = self._format_for_agent(dialogue_data, speaker_mapping)
        
        return formatted_content, speaker_mapping, True
    
    def _parse_text_to_dialogue(self, content: str) -> List[Dict]:
        """텍스트를 대화 데이터로 파싱"""
        lines = content.strip().split('\n')
        dialogue_data = []
        current_time = 0
        
        # 대화 패턴들
        patterns = [
            r'^([가-힣A-Za-z0-9_]+)\s*:\s*(.+)$',  # 화자: 내용
            r'^([가-힣A-Za-z0-9_]+)\s*-\s*(.+)$',  # 화자- 내용
            r'^\[([가-힣A-Za-z0-9_]+)\]\s*(.+)$',  # [화자] 내용
            r'^(\w+)\s*>\s*(.+)$',                 # 화자> 내용
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 패턴 매칭 시도
            matched = False
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    speaker_name = match.group(1)
                    text_content = match.group(2)
                    
                    dialogue_data.append({
                        'speaker_name': speaker_name,
                        'text': text_content.strip(),
                        'start_time': current_time
                    })
                    
                    current_time += 10  # 10초씩 증가
                    matched = True
                    break
            
            # 패턴이 없으면 기본 화자로 처리
            if not matched and line:
                dialogue_data.append({
                    'speaker_name': '사용자',
                    'text': line,
                    'start_time': current_time
                })
                current_time += 10
        
        return dialogue_data
    
    def _create_speaker_mapping(self, dialogue_data: List[Dict]) -> Dict:
        """화자 매핑 생성 (사용자 선택 대기 상태)"""
        # 순서 보장을 위해 첫 등장 순서대로 화자 리스트 생성
        unique_speakers = []
        seen = set()
        for item in dialogue_data:
            speaker = item['speaker_name']
            if speaker not in seen:
                unique_speakers.append(speaker)
                seen.add(speaker)
        
        speaker_mapping = {
            "speaker_names": {},
            "user_ids": {}  # 사용자가 매핑할 때까지 빈 상태
        }
        
        # 화자들을 순서대로 번호 매핑 (사용자 ID는 나중에 설정)
        for i, speaker in enumerate(unique_speakers, start=1):
            speaker_mapping["speaker_names"][str(i)] = speaker
        
        return speaker_mapping
    
    def _format_for_agent(self, dialogue_data: List[Dict], speaker_mapping: Dict) -> str:
        """Agent가 기대하는 형식으로 변환"""
        formatted_lines = []
        
        # 역매핑: speaker_name -> speaker_id
        name_to_id = {v: k for k, v in speaker_mapping["speaker_names"].items()}
        
        for item in dialogue_data:
            speaker_name = item['speaker_name']
            speaker_id = name_to_id.get(speaker_name, "1")
            
            # 시간 포맷팅
            start_time = item['start_time']
            minutes = int(start_time // 60)
            seconds = int(start_time % 60)
            timestamp = f"{minutes:02d}:{seconds:02d}"
            
            formatted_lines.append(f"참석자 {speaker_id} {timestamp}")
            formatted_lines.append(item['text'])
            formatted_lines.append("")  # 빈 줄
        
        return '\n'.join(formatted_lines)


def update_conversation_with_mapping(db, conversation_id: str, user_mapping: Dict[str, int]):
    """사용자 매핑 업데이트 후 conversation content 재생성"""
    from .models import Conversation
    from .file_models import ConversationFile
    
    # conversation과 file 조회
    conversation = db.query(Conversation).filter(Conversation.conv_id == conversation_id).first()
    conv_file = db.query(ConversationFile).filter(ConversationFile.conv_id == conversation_id).first()
    
    if not conversation or not conv_file:
        return False
    
    # 기존 speaker_mapping 업데이트
    current_mapping = conv_file.speaker_mapping or {"speaker_names": {}, "user_ids": {}}
    current_mapping["user_ids"].update(user_mapping)
    conv_file.speaker_mapping = current_mapping
    
    # conversation content에서 화자 ID를 user_id로 치환
    content_lines = conversation.content.split('\n')
    updated_lines = []
    
    for line in content_lines:
        if line.startswith('참석자'):
            parts = line.split()
            if len(parts) >= 2:
                speaker_id = parts[1]
                if speaker_id in user_mapping:
                    # 화자 ID를 실제 user_id로 치환
                    parts[1] = str(user_mapping[speaker_id])
                    line = ' '.join(parts)
        updated_lines.append(line)
    
    conversation.content = '\n'.join(updated_lines)
    db.commit()
    return True
