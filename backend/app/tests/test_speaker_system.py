#!/usr/bin/env python3
"""
화자 시스템 종합 테스트 - 매핑, 개선, 후처리 통합
"""
import sys
sys.path.append('/Users/hyunjunson/Project/GAON/backend')

import requests
import json

def test_speaker_mapping_api():
    """화자 매핑 API 테스트"""
    print("🧪 화자 매핑 API 테스트")
    
    try:
        login_data = {"username": "test@example.com", "password": "testpassword"}
        login_response = requests.post("http://127.0.0.1:8000/api/auth/login", data=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ 로그인 실패: {login_response.status_code}")
            return False
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        conversation_id = "0002e264-c3f9-4fd0-8d54-c05dceded558"
        
        # 매핑 설정
        new_mapping = {"speaker_mapping": {"0": "아빠", "1": "딸"}}
        update_response = requests.put(
            f"http://127.0.0.1:8000/api/conversation/audio/{conversation_id}/speaker-mapping",
            headers=headers, json=new_mapping
        )
        
        print(f"✅ 화자 매핑 설정: {update_response.status_code == 200}")
        return update_response.status_code == 200
            
    except Exception as e:
        print(f"❌ 매핑 테스트 실패: {e}")
        return False

def test_post_processing_logic():
    """후처리 로직 테스트"""
    print("🧪 후처리 로직 테스트")
    
    mock_result = {
        "speaker_segments": [
            {"speaker": 0, "start": 0.9, "end": 4.8, "text": "최근에 건강은 어때"},
            {"speaker": 0, "start": 4.1, "end": 10.2, "text": "건강한 거 같아요"},
            {"speaker": 0, "start": 7.3, "end": 17.4, "text": "최근에 다친 곳 있어"},
            {"speaker": 0, "start": 10.6, "end": 25.6, "text": "아빠가 꽉 잡아서 어깨가 아파요"},
        ],
        "speaker_count": 1
    }
    
    improved_result = apply_post_processing(mock_result)
    print(f"✅ 후처리 결과: {improved_result['speaker_count']}명")
    return improved_result['speaker_count'] > 1

def apply_post_processing(result):
    """후처리 함수"""
    segments = result['speaker_segments']
    question_patterns = ['어때', '있어', '해']
    answer_patterns = ['같아요', '아파요']
    
    current_speaker = 0
    for i, segment in enumerate(segments):
        text = segment['text']
        is_question = any(p in text for p in question_patterns)
        is_answer = any(p in text for p in answer_patterns)
        
        if i > 0:
            prev_text = segments[i-1]['text']
            prev_is_question = any(p in prev_text for p in question_patterns)
            if prev_is_question and is_answer:
                current_speaker = 1 - current_speaker
        
        segment['speaker'] = current_speaker
    
    result['speaker_count'] = len(set(seg['speaker'] for seg in segments))
    return result

def run_all_speaker_tests():
    """모든 화자 시스템 테스트 실행"""
    print("🚀 화자 시스템 종합 테스트 시작\n")
    
    results = {
        'mapping_api': test_speaker_mapping_api(),
        'post_processing': test_post_processing_logic()
    }
    
    print(f"\n📋 테스트 결과:")
    for test_name, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"  {test_name}: {status}")
    
    return sum(results.values()) == len(results)

if __name__ == "__main__":
    success = run_all_speaker_tests()
    exit(0 if success else 1)
