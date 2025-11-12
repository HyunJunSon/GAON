#!/usr/bin/env python3
"""
STT LongRunning API 테스트
"""
import sys
import os
sys.path.append('/Users/hyunjunson/Project/GAON/backend')

from app.domains.conversation.stt_service import STTService
from google.cloud import storage
import json

def test_stt_longrunning():
    """STT LongRunning API 테스트"""
    print("🧪 STT LongRunning API 테스트 시작")
    
    try:
        # GCS에서 테스트 파일 다운로드
        storage_client = storage.Client()
        bucket = storage_client.bucket('gaon-cloud-data')
        blob = bucket.blob('user-upload-conv-data/conversations/user_48/9610873a-9f55-41f8-8b91-a3910346a90b.mp3')
        
        if not blob.exists():
            print("❌ 테스트 파일이 존재하지 않습니다")
            return False
        
        audio_content = blob.download_as_bytes()
        print(f"✅ 테스트 파일 로드: {len(audio_content)} bytes")
        
        # STT 서비스 테스트
        stt_service = STTService()
        result = stt_service.transcribe_audio_with_diarization(audio_content, "0280.mp3")
        
        # 결과 검증
        print(f"📊 STT 결과:")
        print(f"- Transcript 길이: {len(result['transcript'])}자")
        print(f"- 화자 수: {result['speaker_count']}명")
        print(f"- 총 시간: {result['duration']}초")
        print(f"- 세그먼트 수: {len(result['speaker_segments'])}개")
        
        if result['transcript']:
            print(f"- 내용 미리보기: {result['transcript'][:100]}...")
            
        if result['speaker_segments']:
            print(f"📝 화자별 발언 샘플:")
            for i, seg in enumerate(result['speaker_segments'][:3]):
                print(f"  화자{seg['speaker']} ({seg['start']:.1f}s-{seg['end']:.1f}s): {seg['text'][:50]}...")
        
        # 성공 조건 체크
        success = (
            len(result['transcript']) > 0 and
            result['speaker_count'] > 0 and
            len(result['speaker_segments']) > 0
        )
        
        if success:
            print("✅ STT LongRunning API 테스트 성공!")
            return True
        else:
            print("❌ STT 결과가 비어있습니다")
            return False
            
    except Exception as e:
        print(f"❌ STT 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    success = test_stt_longrunning()
    exit(0 if success else 1)
