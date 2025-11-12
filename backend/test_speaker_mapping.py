#!/usr/bin/env python3
"""
화자 매핑 API 테스트
"""
import requests
import json

def test_speaker_mapping():
    """화자 매핑 API 테스트"""
    print("🧪 화자 매핑 API 테스트 시작")
    
    try:
        # 1. 로그인
        login_data = {
            "username": "test@example.com", 
            "password": "testpassword"
        }
        
        login_response = requests.post(
            "http://127.0.0.1:8000/api/auth/login",
            data=login_data
        )
        
        if login_response.status_code != 200:
            print(f"❌ 로그인 실패: {login_response.status_code}")
            return False
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ 로그인 성공")
        
        # 2. 최근 음성 대화 조회 (테스트용)
        # 실제로는 앞서 업로드한 conversation_id 사용
        conversation_id = "0002e264-c3f9-4fd0-8d54-c05dceded558"  # 앞서 테스트에서 생성된 ID
        
        # 3. 현재 화자 매핑 상태 조회
        mapping_response = requests.get(
            f"http://127.0.0.1:8000/api/conversation/audio/{conversation_id}/speaker-mapping",
            headers=headers
        )
        
        if mapping_response.status_code != 200:
            print(f"❌ 화자 매핑 조회 실패: {mapping_response.status_code}")
            print(mapping_response.text)
            return False
        
        current_mapping = mapping_response.json()
        print("✅ 현재 화자 매핑 조회 성공")
        print(f"- 화자 수: {current_mapping['speaker_count']}")
        print(f"- 현재 매핑: {current_mapping['speaker_mapping']}")
        print(f"- 세그먼트 수: {len(current_mapping['mapped_segments'])}")
        
        # 4. 화자 매핑 설정
        new_mapping = {
            "speaker_mapping": {
                "0": "아빠",
                "1": "딸"
            }
        }
        
        update_response = requests.put(
            f"http://127.0.0.1:8000/api/conversation/audio/{conversation_id}/speaker-mapping",
            headers=headers,
            json=new_mapping
        )
        
        if update_response.status_code != 200:
            print(f"❌ 화자 매핑 설정 실패: {update_response.status_code}")
            print(update_response.text)
            return False
        
        update_result = update_response.json()
        print("✅ 화자 매핑 설정 성공")
        print(f"- 설정된 매핑: {update_result['speaker_mapping']}")
        
        # 5. 설정 후 다시 조회하여 확인
        final_response = requests.get(
            f"http://127.0.0.1:8000/api/conversation/audio/{conversation_id}/speaker-mapping",
            headers=headers
        )
        
        if final_response.status_code != 200:
            print(f"❌ 최종 확인 실패: {final_response.status_code}")
            return False
        
        final_mapping = final_response.json()
        print("✅ 최종 확인 성공")
        print(f"- 저장된 매핑: {final_mapping['speaker_mapping']}")
        
        # 6. 매핑된 세그먼트 샘플 출력
        if final_mapping['mapped_segments']:
            print("📝 매핑된 대화 샘플:")
            for i, segment in enumerate(final_mapping['mapped_segments'][:5]):
                speaker_name = segment['speaker_name'] or f"화자{segment['speaker']}"
                print(f"  {speaker_name} ({segment['start']:.1f}s-{segment['end']:.1f}s): {segment['text'][:50]}...")
        
        # 성공 조건 체크
        success = (
            final_mapping['speaker_mapping'].get('0') == '아빠' and
            final_mapping['speaker_mapping'].get('1') == '딸' and
            len(final_mapping['mapped_segments']) > 0
        )
        
        if success:
            print("✅ 화자 매핑 API 테스트 성공!")
            return True
        else:
            print("❌ 화자 매핑이 올바르게 저장되지 않았습니다")
            return False
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    success = test_speaker_mapping()
    exit(0 if success else 1)
