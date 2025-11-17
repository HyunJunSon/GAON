import pytest
from app.domains.conversation.text_mapping_service import TextMappingService


class TestTextMappingService:
    
    def setup_method(self):
        self.service = TextMappingService()
    
    def test_dialogue_format_parsing(self):
        """대화 형식 파싱 테스트"""
        content = """아빠: 오늘 날씨가 좋네요
딸: 네, 정말 좋아요
아빠: 산책하러 갈까?
딸: 좋아요!"""
        
        formatted_content, speaker_mapping, can_analyze = self.service.apply_speaker_mapping_to_text(content, 123)
        
        assert can_analyze == True
        assert "참석자 1 00:00" in formatted_content
        assert "참석자 2 00:10" in formatted_content
        assert speaker_mapping["speaker_names"]["1"] == "아빠"
        assert speaker_mapping["speaker_names"]["2"] == "딸"
        assert speaker_mapping["user_ids"] == {}  # 사용자 매핑 대기 상태
    
    def test_bracket_format_parsing(self):
        """대괄호 형식 파싱 테스트"""
        content = """[엄마] 저녁 뭐 먹을까?
[아들] 치킨 어때요?
[엄마] 좋은 생각이야"""
        
        formatted_content, speaker_mapping, can_analyze = self.service.apply_speaker_mapping_to_text(content, 456)
        
        assert can_analyze == True
        assert speaker_mapping["speaker_names"]["1"] == "엄마"
        assert speaker_mapping["speaker_names"]["2"] == "아들"
        assert speaker_mapping["user_ids"] == {}  # 사용자 매핑 대기 상태
    
    def test_single_speaker_rejection(self):
        """단일 화자 텍스트 거부 테스트"""
        content = """오늘은 정말 좋은 날이었다.
아침에 일찍 일어나서 운동을 했다.
점심에는 맛있는 음식을 먹었다."""
        
        formatted_content, speaker_mapping, can_analyze = self.service.apply_speaker_mapping_to_text(content, 789)
        
        assert can_analyze == False
        assert formatted_content == ""
        assert speaker_mapping == {}
    
    def test_mixed_format_parsing(self):
        """혼합 형식 파싱 테스트"""
        content = """사용자: 안녕하세요
상대방- 안녕하세요
사용자> 오늘 어떠세요?
[상대방] 좋아요"""
        
        formatted_content, speaker_mapping, can_analyze = self.service.apply_speaker_mapping_to_text(content, 111)
        
        assert can_analyze == True
        assert len(speaker_mapping["speaker_names"]) == 2
        assert speaker_mapping["user_ids"] == {}  # 사용자 매핑 대기 상태
    
    def test_plain_text_single_speaker(self):
        """패턴 없는 단일 화자 텍스트"""
        content = """이것은 일반적인 텍스트입니다.
화자 구분이 없습니다.
분석이 불가능해야 합니다."""
        
        formatted_content, speaker_mapping, can_analyze = self.service.apply_speaker_mapping_to_text(content, 222)
        
        assert can_analyze == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
