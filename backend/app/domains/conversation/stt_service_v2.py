import logging
from typing import List, Dict, Any, Optional
from google.cloud import speech
from google.cloud.speech import RecognitionAudio, RecognitionConfig, SpeakerDiarizationConfig
import io

logger = logging.getLogger(__name__)


class STTServiceV2:
    """Google Cloud Speech-to-Text API v2 with Chirp model"""
    
    def __init__(self):
        """STT 서비스 초기화"""
        try:
            self.client = speech.SpeechClient()
            logger.info("Google Cloud Speech-to-Text v2 클라이언트 초기화 완료")
        except Exception as e:
            logger.error(f"STT 클라이언트 초기화 실패: {str(e)}")
            raise
    
    def transcribe_audio_with_diarization(
        self, 
        audio_content: bytes, 
        filename: str,
        language_code: str = "ko-KR",
        max_speakers: int = 2
    ) -> Dict[str, Any]:
        """Chirp 모델을 사용한 향상된 화자분리"""
        try:
            encoding, sample_rate = self._get_audio_config(filename)
            file_size_mb = len(audio_content) / (1024 * 1024)
            
            logger.info(f"STT v2 처리 시작 - 파일: {filename}, 크기: {file_size_mb:.1f}MB")
            
            if file_size_mb > 1.0:
                return self._transcribe_long_audio_v2(audio_content, encoding, sample_rate, language_code, max_speakers)
            else:
                return self._transcribe_short_audio_v2(audio_content, encoding, sample_rate, language_code, max_speakers)
                
        except Exception as e:
            logger.error(f"STT 처리 실패: {str(e)}")
            raise
    
    def _transcribe_short_audio_v2(self, audio_content: bytes, encoding, sample_rate: int,
                                  language_code: str, max_speakers: int) -> Dict[str, Any]:
        """Chirp 모델을 사용한 짧은 오디오 처리"""
        audio = RecognitionAudio(content=audio_content)
        
        # 향상된 화자분리 설정
        diarization_config = SpeakerDiarizationConfig(
            enable_speaker_diarization=True,
            min_speaker_count=1,  # 최소 1명으로 설정
            max_speaker_count=max_speakers,
        )
        
        config = RecognitionConfig(
            encoding=encoding,
            sample_rate_hertz=sample_rate,
            language_code=language_code,
            diarization_config=diarization_config,
            enable_automatic_punctuation=True,
            use_enhanced=True,
            model="chirp",  # Chirp 모델 사용
            enable_word_time_offsets=True,
        )
        
        response = self.client.recognize(config=config, audio=audio)
        return self._parse_recognition_response(response)
    
    def _transcribe_long_audio_v2(self, audio_content: bytes, encoding, sample_rate: int,
                                 language_code: str, max_speakers: int) -> Dict[str, Any]:
        """Chirp 모델을 사용한 긴 오디오 처리"""
        from google.cloud import storage
        import uuid
        import time
        
        try:
            bucket_name = "gaon-cloud-data"
            temp_filename = f"temp-audio/{uuid.uuid4()}.audio"
            
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(temp_filename)
            blob.upload_from_string(audio_content)
            
            gcs_uri = f"gs://{bucket_name}/{temp_filename}"
            
            # Chirp 모델로 LongRunning 요청
            diarization_config = SpeakerDiarizationConfig(
                enable_speaker_diarization=True,
                min_speaker_count=1,
                max_speaker_count=max_speakers,
            )
            
            config = RecognitionConfig(
                encoding=encoding,
                sample_rate_hertz=sample_rate,
                language_code=language_code,
                diarization_config=diarization_config,
                enable_automatic_punctuation=True,
                use_enhanced=True,
                model="chirp",  # Chirp 모델 사용
                enable_word_time_offsets=True,
            )
            
            audio = RecognitionAudio(uri=gcs_uri)
            operation = self.client.long_running_recognize(config=config, audio=audio)
            
            logger.info("LongRunning 작업 시작, 완료 대기 중...")
            response = operation.result(timeout=600)
            
            # 임시 파일 정리
            blob.delete()
            logger.info("임시 GCS 파일 정리 완료")
            
            return self._parse_recognition_response(response)
            
        except Exception as e:
            logger.error(f"LongRunning STT 처리 실패: {str(e)}")
            raise
    
    def _get_audio_config(self, filename: str):
        """파일 확장자에 따른 오디오 설정 반환"""
        ext = filename.lower().split('.')[-1]
        
        if ext in ['mp3', 'mpeg']:
            return speech.RecognitionConfig.AudioEncoding.MP3, 16000
        elif ext in ['wav', 'wave']:
            return speech.RecognitionConfig.AudioEncoding.LINEAR16, 16000
        elif ext in ['webm']:
            return speech.RecognitionConfig.AudioEncoding.WEBM_OPUS, 48000
        elif ext in ['flac']:
            return speech.RecognitionConfig.AudioEncoding.FLAC, 16000
        else:
            return speech.RecognitionConfig.AudioEncoding.LINEAR16, 16000
    
    def _parse_recognition_response(self, response) -> Dict[str, Any]:
        """STT 응답 파싱 및 화자분리 정보 추출"""
        if not response.results:
            return {
                "transcript": "",
                "speaker_segments": [],
                "duration": 0,
                "speaker_count": 0
            }
        
        # 전체 텍스트 추출
        transcript = ""
        speaker_segments = []
        speakers = set()
        
        for result in response.results:
            if result.alternatives:
                alternative = result.alternatives[0]
                transcript += alternative.transcript + " "
                
                # 화자별 세그먼트 추출
                for word in alternative.words:
                    if hasattr(word, 'speaker_tag') and word.speaker_tag:
                        speakers.add(word.speaker_tag)
        
        # 화자별 세그먼트 재구성
        current_speaker = None
        current_text = ""
        current_start = None
        current_end = None
        
        for result in response.results:
            if result.alternatives:
                for word in result.alternatives[0].words:
                    speaker = getattr(word, 'speaker_tag', 0)
                    word_text = word.word
                    start_time = word.start_time.total_seconds() if word.start_time else 0
                    end_time = word.end_time.total_seconds() if word.end_time else 0
                    
                    if current_speaker != speaker:
                        # 이전 세그먼트 저장
                        if current_text.strip():
                            speaker_segments.append({
                                "speaker": current_speaker or 0,
                                "text": current_text.strip(),
                                "start": current_start or 0,
                                "end": current_end or 0
                            })
                        
                        # 새 세그먼트 시작
                        current_speaker = speaker
                        current_text = word_text
                        current_start = start_time
                        current_end = end_time
                    else:
                        current_text += " " + word_text
                        current_end = end_time
        
        # 마지막 세그먼트 저장
        if current_text.strip():
            speaker_segments.append({
                "speaker": current_speaker or 0,
                "text": current_text.strip(),
                "start": current_start or 0,
                "end": current_end or 0
            })
        
        # 총 시간 계산
        duration = max([seg["end"] for seg in speaker_segments]) if speaker_segments else 0
        
        return {
            "transcript": transcript.strip(),
            "speaker_segments": speaker_segments,
            "duration": duration,
            "speaker_count": len(speakers) if speakers else 1
        }
