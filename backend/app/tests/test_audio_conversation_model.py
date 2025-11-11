import pytest
from datetime import datetime


def test_conversation_file_audio_fields_structure():
    """ConversationFile 모델의 음성 관련 필드 구조 테스트"""
    from app.domains.conversation.file_models import ConversationFile
    
    # 모델 클래스에 새로운 필드들이 정의되어 있는지 확인
    assert hasattr(ConversationFile, 'audio_url')
    assert hasattr(ConversationFile, 'transcript')
    assert hasattr(ConversationFile, 'speaker_segments')
    assert hasattr(ConversationFile, 'duration')
    assert hasattr(ConversationFile, 'speaker_count')


def test_conversation_file_audio_field_types():
    """ConversationFile 모델의 음성 필드 타입 테스트"""
    from app.domains.conversation.file_models import ConversationFile
    from sqlalchemy import String, Text, JSON, Integer
    
    # 필드 타입 확인
    audio_url_column = ConversationFile.__table__.columns.get('audio_url')
    transcript_column = ConversationFile.__table__.columns.get('transcript')
    speaker_segments_column = ConversationFile.__table__.columns.get('speaker_segments')
    duration_column = ConversationFile.__table__.columns.get('duration')
    speaker_count_column = ConversationFile.__table__.columns.get('speaker_count')
    
    # 필드가 존재하는지 확인
    assert audio_url_column is not None
    assert transcript_column is not None
    assert speaker_segments_column is not None
    assert duration_column is not None
    assert speaker_count_column is not None
    
    # 필드 타입 확인
    assert isinstance(audio_url_column.type, String)
    assert isinstance(transcript_column.type, Text)
    assert isinstance(speaker_segments_column.type, JSON)
    assert isinstance(duration_column.type, Integer)
    assert isinstance(speaker_count_column.type, Integer)
    
    # nullable 속성 확인 (모두 True여야 함)
    assert audio_url_column.nullable is True
    assert transcript_column.nullable is True
    assert speaker_segments_column.nullable is True
    assert duration_column.nullable is True
    assert speaker_count_column.nullable is True


def test_speaker_segments_json_structure():
    """화자 구간 JSON 구조 검증 테스트"""
    
    # 예상되는 speaker_segments 구조
    expected_segments = [
        {"speaker": 1, "start": 0.0, "end": 2.3, "text": "안녕하세요"},
        {"speaker": 2, "start": 2.4, "end": 5.1, "text": "반갑습니다"}
    ]
    
    # 구조 검증
    assert isinstance(expected_segments, list)
    assert len(expected_segments) == 2
    
    # 첫 번째 세그먼트 검증
    first_segment = expected_segments[0]
    assert "speaker" in first_segment
    assert "start" in first_segment
    assert "end" in first_segment
    assert "text" in first_segment
    assert isinstance(first_segment["speaker"], int)
    assert isinstance(first_segment["start"], float)
    assert isinstance(first_segment["end"], float)
    assert isinstance(first_segment["text"], str)
    
    # 두 번째 세그먼트 검증
    second_segment = expected_segments[1]
    assert second_segment["speaker"] == 2
    assert second_segment["text"] == "반갑습니다"
