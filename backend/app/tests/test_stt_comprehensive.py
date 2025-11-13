#!/usr/bin/env python3
"""
STT 서비스 종합 테스트 - 작은 파일, 큰 파일, LongRunning API 통합
"""
import sys
import os
sys.path.append('/Users/hyunjunson/Project/GAON/backend')

from app.domains.conversation.stt_service import STTService
from google.cloud import storage
import json

def test_small_webm_file():
    """작은 webm 파일로 STT 테스트"""
    print("🧪 작은 webm 파일 STT 테스트")
    
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket('gaon-cloud-data')
        blob = bucket.blob('user-upload-conv-data/conversations/user_9/b29c8531-3932-41c4-80f5-cde4928d28ef.webm')
        
        if not blob.exists():
            print("❌ webm 테스트 파일이 존재하지 않습니다")
            return False
        
        audio_content = blob.download_as_bytes()
        print(f"✅ webm 파일 로드: {len(audio_content)} bytes")
        
        stt_service = STTService()
        result = stt_service.transcribe_audio_with_diarization(audio_content, "test.webm")
        
        print(f"📊 webm STT 결과: {len(result['transcript'])}자, {result['speaker_count']}명, {len(result['speaker_segments'])}개 세그먼트")
        return True
            
    except Exception as e:
        print(f"❌ webm STT 테스트 실패: {e}")
        return False

def test_large_mp3_longrunning():
    """큰 mp3 파일로 LongRunning API 테스트"""
    print("🧪 큰 mp3 파일 LongRunning API 테스트")
    
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket('gaon-cloud-data')
        blob = bucket.blob('user-upload-conv-data/conversations/user_48/9610873a-9f55-41f8-8b91-a3910346a90b.mp3')
        
        if not blob.exists():
            print("❌ mp3 테스트 파일이 존재하지 않습니다")
            return False
        
        audio_content = blob.download_as_bytes()
        print(f"✅ mp3 파일 로드: {len(audio_content)} bytes")
        
        stt_service = STTService()
        result = stt_service.transcribe_audio_with_diarization(audio_content, "large_test.mp3")
        
        print(f"📊 mp3 STT 결과: {len(result['transcript'])}자, {result['speaker_count']}명, {len(result['speaker_segments'])}개 세그먼트")
        
        if result['speaker_segments']:
            speakers = {}
            for seg in result['speaker_segments']:
                speakers[seg['speaker']] = speakers.get(seg['speaker'], 0) + 1
            print(f"📝 화자별 발언 수: {speakers}")
        
        return len(result['transcript']) > 0 and result['speaker_count'] > 0
            
    except Exception as e:
        print(f"❌ mp3 STT 테스트 실패: {e}")
        return False

def test_local_wav_file():
    """로컬 wav 파일로 STT 테스트"""
    print("🧪 로컬 wav 파일 STT 테스트")
    
    try:
        audio_path = "/Users/hyunjunson/Project/GAON/data/test_audio/audio/4507-16021-0012.wav"
        
        if not os.path.exists(audio_path):
            print("❌ wav 테스트 파일이 존재하지 않습니다")
            return False
        
        with open(audio_path, 'rb') as f:
            audio_content = f.read()
            
        print(f"✅ wav 파일 로드: {len(audio_content)} bytes")
        
        stt_service = STTService()
        result = stt_service.transcribe_audio_with_diarization(audio_content, "test.wav")
        
        print(f"📊 wav STT 결과: {len(result['transcript'])}자, {result['speaker_count']}명, {len(result['speaker_segments'])}개 세그먼트")
        return True
            
    except Exception as e:
        print(f"❌ wav STT 테스트 실패: {e}")
        return False

def run_all_stt_tests():
    """모든 STT 테스트 실행"""
    print("🚀 STT 종합 테스트 시작\n")
    
    results = {
        'webm': test_small_webm_file(),
        'mp3_longrunning': test_large_mp3_longrunning(), 
        'wav': test_local_wav_file()
    }
    
    print(f"\n📋 테스트 결과:")
    for test_name, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"  {test_name}: {status}")
    
    total_success = sum(results.values())
    print(f"\n🎯 전체 결과: {total_success}/{len(results)} 성공")
    
    return total_success == len(results)

if __name__ == "__main__":
    success = run_all_stt_tests()
    exit(0 if success else 1)
