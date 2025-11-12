import logging
from typing import List, Dict, Any, Optional
from google.cloud import speech
from google.cloud.speech import RecognitionAudio, RecognitionConfig, SpeakerDiarizationConfig
import io

logger = logging.getLogger(__name__)


class STTService:
    """Google Cloud Speech-to-Text API를 사용한 음성 인식 서비스"""
    
    def __init__(self):
        """STT 서비스 초기화"""
        try:
            self.client = speech.SpeechClient()
            logger.info("Google Cloud Speech-to-Text 클라이언트 초기화 완료")
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
        """
        음성 파일을 텍스트로 변환하고 화자를 구분합니다.
        
        Args:
            audio_content: 오디오 파일의 바이트 데이터
            filename: 파일명 (확장자로 형식 판단)
            language_code: 언어 코드 (기본값: "ko-KR")
            max_speakers: 최대 화자 수 (기본값: 2)
            
        Returns:
            Dict containing transcript, speaker_segments, duration, speaker_count
        """
        try:
            # 파일 형식에 따른 인코딩 및 샘플 레이트 설정
            encoding, sample_rate = self._get_audio_config(filename)
            
            # 파일 크기 기준으로 LongRunning API 사용 결정 (10MB 이상)
            file_size_mb = len(audio_content) / (1024 * 1024)
            
            logger.info(f"STT 처리 시작 - 파일: {filename}, 크기: {file_size_mb:.1f}MB")
            
            # 1MB 이상이면 LongRunning API 사용
            if file_size_mb > 1:
                return self._transcribe_long_audio(audio_content, encoding, sample_rate, language_code, max_speakers)
            else:
                return self._transcribe_short_audio(audio_content, encoding, sample_rate, language_code, max_speakers)
            
        except Exception as e:
            logger.error(f"STT 처리 실패: {str(e)}")
            return {
                "transcript": "",
                "speaker_segments": [],
                "duration": 0,
                "speaker_count": 0
            }
    
    def _get_audio_config(self, filename: str) -> tuple:
        """파일 확장자에 따른 오디오 설정 반환"""
        ext = filename.lower().split('.')[-1]
        
        config_map = {
            'mp3': (RecognitionConfig.AudioEncoding.MP3, 44100),
            'wav': (RecognitionConfig.AudioEncoding.LINEAR16, 16000),
            'webm': (RecognitionConfig.AudioEncoding.WEBM_OPUS, 48000),
            'm4a': (RecognitionConfig.AudioEncoding.MP3, 44100),  # M4A를 MP3로 처리
        }
        
        return config_map.get(ext, (RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED, 16000))
    
    def _transcribe_short_audio(self, audio_content: bytes, encoding, sample_rate: int, 
                               language_code: str, max_speakers: int) -> Dict[str, Any]:
        """짧은 오디오 (1분 미만) 처리"""
        audio = RecognitionAudio(content=audio_content)
        
        diarization_config = SpeakerDiarizationConfig(
            enable_speaker_diarization=True,
            min_speaker_count=2,  # 최소 화자 수 명시
            max_speaker_count=max_speakers,
        )
        
        config = RecognitionConfig(
            encoding=encoding,
            sample_rate_hertz=sample_rate,
            language_code=language_code,
            diarization_config=diarization_config,
            enable_automatic_punctuation=True,
        )
        
        response = self.client.recognize(config=config, audio=audio)
        return self._parse_recognition_response(response)
    
    def _transcribe_long_audio(self, audio_content: bytes, encoding, sample_rate: int,
                              language_code: str, max_speakers: int) -> Dict[str, Any]:
        """긴 오디오 (1분 이상) 처리 - GCS 업로드 후 LongRunning API 사용"""
        from google.cloud import storage
        import uuid
        import time
        
        try:
            # 임시 GCS 경로에 업로드
            bucket_name = "gaon-cloud-data"
            temp_filename = f"temp-audio/{uuid.uuid4()}.audio"
            
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(temp_filename)
            blob.upload_from_string(audio_content)
            
            gcs_uri = f"gs://{bucket_name}/{temp_filename}"
            logger.info(f"긴 오디오 파일을 GCS에 업로드: {gcs_uri}")
            
            # LongRunning API 설정
            audio = RecognitionAudio(uri=gcs_uri)
            
            diarization_config = SpeakerDiarizationConfig(
                enable_speaker_diarization=True,
                min_speaker_count=2,  # 최소 화자 수 명시
                max_speaker_count=max_speakers,
            )
            
            config = RecognitionConfig(
                encoding=encoding,
                sample_rate_hertz=sample_rate,
                language_code=language_code,
                diarization_config=diarization_config,
                enable_automatic_punctuation=True,
                model="latest_long"
            )
            
            # LongRunning 요청 시작
            operation = self.client.long_running_recognize(config=config, audio=audio)
            logger.info("LongRunning STT 작업 시작, 완료 대기 중...")
            
            # 결과 대기 (최대 10분)
            response = operation.result(timeout=600)
            
            # 임시 파일 삭제
            try:
                blob.delete()
                logger.info("임시 GCS 파일 삭제 완료")
            except:
                pass
            
            return self._parse_recognition_response(response)
            
        except Exception as e:
            logger.error(f"LongRunning STT 처리 실패: {str(e)}")
            # 임시 파일 정리 시도
            try:
                blob.delete()
            except:
                pass
            raise
    
    def _parse_recognition_response(self, response) -> Dict[str, Any]:
        """
        Google STT API 응답을 파싱하여 구조화된 데이터로 변환
        
        Args:
            response: Google STT API 응답 객체
            
        Returns:
            Dict containing parsed transcript and speaker information
        """
        try:
            # 전체 텍스트 추출
            transcript_parts = []
            speaker_segments = []
            speakers_detected = set()
            
            # 각 결과에서 대안 중 첫 번째(가장 확률 높은) 선택
            for result in response.results:
                alternative = result.alternatives[0]
                transcript_parts.append(alternative.transcript)
                
                # 화자 정보가 있는 경우 처리
                if hasattr(alternative, 'words') and alternative.words:
                    current_speaker = None
                    current_text = []
                    start_time = None
                    
                    for word_info in alternative.words:
                        speaker_tag = word_info.speaker_tag
                        speakers_detected.add(speaker_tag)
                        
                        # 새로운 화자가 시작되는 경우
                        if current_speaker != speaker_tag:
                            # 이전 화자의 세그먼트 저장
                            if current_speaker is not None and current_text:
                                end_time = word_info.start_time.total_seconds()
                                speaker_segments.append({
                                    "speaker": current_speaker,
                                    "start": start_time,
                                    "end": end_time,
                                    "text": " ".join(current_text).strip()
                                })
                            
                            # 새로운 화자 세그먼트 시작
                            current_speaker = speaker_tag
                            current_text = [word_info.word]
                            start_time = word_info.start_time.total_seconds()
                        else:
                            # 같은 화자의 단어 추가
                            current_text.append(word_info.word)
                    
                    # 마지막 세그먼트 저장
                    if current_speaker is not None and current_text:
                        # 마지막 단어의 종료 시간 계산
                        last_word = alternative.words[-1]
                        end_time = (last_word.start_time.total_seconds() + 
                                  last_word.end_time.total_seconds())
                        
                        speaker_segments.append({
                            "speaker": current_speaker,
                            "start": start_time,
                            "end": end_time,
                            "text": " ".join(current_text).strip()
                        })
            
            # 전체 텍스트 결합
            full_transcript = " ".join(transcript_parts).strip()
            
            # 총 시간 계산 (마지막 세그먼트의 종료 시간)
            duration = max([seg["end"] for seg in speaker_segments]) if speaker_segments else 0
            
            # 화자 수
            speaker_count = len(speakers_detected)
            
            result = {
                "transcript": full_transcript,
                "speaker_segments": speaker_segments,
                "duration": int(duration),
                "speaker_count": speaker_count
            }
            
            logger.info(f"STT 처리 완료 - 화자 수: {speaker_count}, 총 시간: {duration}초")
            return result
            
        except Exception as e:
            logger.error(f"STT 응답 파싱 실패: {str(e)}")
            raise Exception(f"음성 인식 결과 처리 중 오류가 발생했습니다: {str(e)}")
    
    def validate_audio_format(self, audio_content: bytes, filename: str) -> bool:
        """
        오디오 파일 형식이 유효한지 검증
        
        Args:
            audio_content: 오디오 파일의 바이트 데이터
            filename: 파일명
            
        Returns:
            bool: 유효한 형식이면 True
        """
        try:
            if len(audio_content) < 4:
                return False
            
            ext = filename.lower().split('.')[-1]
            
            # 파일 시그니처 검증
            signatures = {
                'mp3': [b'ID3', b'\xff\xfb', b'\xff\xf3', b'\xff\xf2'],  # MP3 시그니처들
                'wav': [b'RIFF'],  # WAV 시그니처
                'webm': [b'\x1a\x45\xdf\xa3'],  # WebM 시그니처
                'm4a': [b'ftyp'],  # M4A 시그니처 (4바이트 오프셋)
            }
            
            if ext in signatures:
                for sig in signatures[ext]:
                    if ext == 'm4a':
                        # M4A는 4바이트 오프셋에서 확인
                        if len(audio_content) >= 8 and audio_content[4:8] == sig:
                            return True
                    else:
                        if audio_content.startswith(sig):
                            return True
                        # MP3의 경우 중간에 시그니처가 있을 수 있음
                        if ext == 'mp3' and sig in audio_content[:1024]:
                            return True
            
            logger.warning(f"지원하지 않는 오디오 형식: {filename}")
            return False
            
        except Exception as e:
            logger.error(f"오디오 형식 검증 실패: {str(e)}")
            return False
