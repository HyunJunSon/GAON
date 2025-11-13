#!/usr/bin/env python3
"""
pyannote.audio 통합 테스트 - WAV 변환 및 화자 분리
"""
import sys
import os
sys.path.append('/Users/hyunjunson/Project/GAON/backend')

from google.cloud import storage
from app.core.config import settings
import tempfile
import subprocess

def test_pyannote_library():
    """pyannote 라이브러리 로드 테스트"""
    print("🧪 pyannote 라이브러리 테스트")
    
    try:
        from pyannote.audio import Pipeline
        print("✅ pyannote.audio 라이브러리 로드 성공")
        return True
    except ImportError as e:
        print(f"❌ pyannote.audio 라이브러리 로드 실패: {e}")
        return False

def test_mp3_to_wav_conversion():
    """MP3를 WAV로 변환 테스트"""
    print("🧪 MP3 -> WAV 변환 테스트")
    
    try:
        # GCS에서 MP3 파일 다운로드
        storage_client = storage.Client()
        bucket = storage_client.bucket('gaon-cloud-data')
        blob = bucket.blob('user-upload-conv-data/conversations/user_48/9610873a-9f55-41f8-8b91-a3910346a90b.mp3')
        
        if not blob.exists():
            print("❌ 테스트 MP3 파일이 존재하지 않습니다")
            return False
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_mp3:
            blob.download_to_filename(temp_mp3.name)
            mp3_path = temp_mp3.name
        
        print(f"✅ MP3 파일 다운로드: {os.path.getsize(mp3_path)} bytes")
        
        # ffmpeg로 WAV 변환
        wav_path = mp3_path.replace('.mp3', '.wav')
        cmd = ['ffmpeg', '-i', mp3_path, '-ar', '16000', '-ac', '1', wav_path, '-y']
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(wav_path):
            print(f"✅ WAV 변환 성공: {os.path.getsize(wav_path)} bytes")
            
            # 정리
            os.unlink(mp3_path)
            os.unlink(wav_path)
            return True
        else:
            print(f"❌ WAV 변환 실패: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 변환 테스트 실패: {e}")
        return False

def test_pyannote_diarization():
    """pyannote로 화자 분리 테스트"""
    print("🧪 pyannote 화자 분리 테스트")
    
    try:
        from pyannote.audio import Pipeline
        
        # Hugging Face 토큰 확인
        if not hasattr(settings, 'huggingface_token') or not settings.huggingface_token:
            print("❌ Hugging Face 토큰이 설정되지 않았습니다")
            return False
        
        # 파이프라인 초기화 시도
        try:
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=settings.huggingface_token
            )
            print("✅ pyannote 파이프라인 초기화 성공")
            return True
        except Exception as e:
            print(f"❌ 파이프라인 초기화 실패: {e}")
            return False
            
    except ImportError:
        print("❌ pyannote.audio 라이브러리가 설치되지 않았습니다")
        return False
    except Exception as e:
        print(f"❌ 화자 분리 테스트 실패: {e}")
        return False

def run_all_pyannote_tests():
    """모든 pyannote 테스트 실행"""
    print("🚀 pyannote 통합 테스트 시작\n")
    
    results = {
        'library_load': test_pyannote_library(),
        'wav_conversion': test_mp3_to_wav_conversion(),
        'diarization': test_pyannote_diarization()
    }
    
    print(f"\n📋 테스트 결과:")
    for test_name, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"  {test_name}: {status}")
    
    total_success = sum(results.values())
    print(f"\n🎯 전체 결과: {total_success}/{len(results)} 성공")
    
    return total_success == len(results)

if __name__ == "__main__":
    success = run_all_pyannote_tests()
    exit(0 if success else 1)
