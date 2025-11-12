#!/usr/bin/env python3
"""
음성 파일 업로드 API 테스트
"""
import requests
import sys
from google.cloud import storage

def test_audio_upload_api():
    """음성 파일 업로드 API 테스트"""
    print("🧪 음성 파일 업로드 API 테스트 시작")
    
    try:
        # 1. 테스트 파일 다운로드
        storage_client = storage.Client()
        bucket = storage_client.bucket('gaon-cloud-data')
        blob = bucket.blob('user-upload-conv-data/conversations/user_48/9610873a-9f55-41f8-8b91-a3910346a90b.mp3')
        
        if not blob.exists():
            print("❌ 테스트 파일이 존재하지 않습니다")
            return False
        
        audio_content = blob.download_as_bytes()
        print(f"✅ 테스트 파일 로드: {len(audio_content)} bytes")
        
        # 2. 임시 사용자 생성 또는 기존 사용자 사용
        # 먼저 사용자 등록 시도
        register_data = {
            "email": "test_audio@example.com",
            "password": "testpassword123",
            "name": "테스트 사용자"
        }
        
        register_response = requests.post(
            "http://127.0.0.1:8000/api/auth/register",
            json=register_data
        )
        
        # 3. 로그인 (form data 형식)
        login_data = {
            "username": "test_audio@example.com", 
            "password": "testpassword123"
        }
        
        login_response = requests.post(
            "http://127.0.0.1:8000/api/auth/login",
            data=login_data
        )
        
        if login_response.status_code != 200:
            print(f"❌ 로그인 실패: {login_response.status_code}")
            print(login_response.text)
            return False
        
        token = login_response.json()["access_token"]
        print("✅ 로그인 성공")
        
        # 4. 음성 파일 업로드
        headers = {"Authorization": f"Bearer {token}"}
        files = {"file": ("test_audio.mp3", audio_content, "audio/mp3")}
        data = {"family_id": 1}
        
        upload_response = requests.post(
            "http://127.0.0.1:8000/api/conversation/audio",
            headers=headers,
            files=files,
            data=data
        )
        
        if upload_response.status_code != 200:
            print(f"❌ 파일 업로드 실패: {upload_response.status_code}")
            print(upload_response.text)
            return False
        
        result = upload_response.json()
        print("✅ 파일 업로드 성공")
        print(f"- Conversation ID: {result['conversation_id']}")
        print(f"- File ID: {result['file_id']}")
        print(f"- Status: {result['status']}")
        
        # 5. 업로드된 대화 상세 조회
        conversation_id = result['conversation_id']
        detail_response = requests.get(
            f"http://127.0.0.1:8000/api/conversation/audio/{conversation_id}",
            headers=headers
        )
        
        if detail_response.status_code != 200:
            print(f"❌ 대화 상세 조회 실패: {detail_response.status_code}")
            return False
        
        detail = detail_response.json()
        print("✅ 대화 상세 조회 성공")
        print(f"- 화자 수: {detail['file_info']['speaker_count']}")
        print(f"- 시간: {detail['file_info']['duration']}초")
        print(f"- 텍스트 길이: {len(detail['transcript']['full_text'])}자")
        print(f"- 세그먼트 수: {len(detail['transcript']['speaker_segments'])}개")
        
        if detail['transcript']['full_text']:
            print(f"- 내용 미리보기: {detail['transcript']['full_text'][:100]}...")
        
        # 성공 조건 체크
        success = (
            detail['file_info']['speaker_count'] > 0 and
            detail['file_info']['duration'] > 0 and
            len(detail['transcript']['full_text']) > 0
        )
        
        if success:
            print("✅ 음성 파일 업로드 API 테스트 성공!")
            return True
        else:
            print("❌ STT 처리 결과가 비어있습니다")
            return False
            
    except Exception as e:
        print(f"❌ API 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    success = test_audio_upload_api()
    exit(0 if success else 1)
