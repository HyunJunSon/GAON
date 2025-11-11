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
        sample_rate: int = 16000,  # 더 일반적인 샘플 레이트
        language_code: str = "ko-KR",
        max_speakers: int = 2
    ) -> Dict[str, Any]:
        """
        음성 파일을 텍스트로 변환하고 화자를 구분합니다.
        
        Args:
            audio_content: 오디오 파일의 바이트 데이터
            sample_rate: 샘플링 레이트 (기본값: 16000Hz)
            language_code: 언어 코드 (기본값: "ko-KR")
            max_speakers: 최대 화자 수 (기본값: 2)
            
        Returns:
            Dict containing transcript, speaker_segments, duration, speaker_count
        """
        try:
            # 오디오 설정
            audio = RecognitionAudio(content=audio_content)
            
            # 화자 구분 설정
            diarization_config = SpeakerDiarizationConfig(
                enable_speaker_diarization=True,
                max_speaker_count=max_speakers,
            )
            
            # 인식 설정 - 자동 인코딩 감지 시도
            config = RecognitionConfig(
                encoding=RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,  # 자동 감지
                sample_rate_hertz=sample_rate,
                language_code=language_code,
                diarization_config=diarization_config,
                enable_automatic_punctuation=True,
                model="latest_long"  # 긴 오디오에 최적화된 모델
            )
            
            logger.info(f"STT 처리 시작 - 언어: {language_code}, 최대 화자: {max_speakers}")
            
            try:
                # 음성 인식 실행
                response = self.client.recognize(config=config, audio=audio)
            except Exception as e:
                # 자동 감지 실패 시 WEBM_OPUS로 재시도
                logger.warning(f"자동 인코딩 감지 실패, WEBM_OPUS로 재시도: {str(e)}")
                config.encoding = RecognitionConfig.AudioEncoding.WEBM_OPUS
                response = self.client.recognize(config=config, audio=audio)
            
            if not response.results:
                logger.warning("STT 결과가 없습니다")
                return {
                    "transcript": "",
                    "speaker_segments": [],
                    "duration": 0,
                    "speaker_count": 0
                }
            
            # 결과 파싱
            return self._parse_recognition_response(response)
            
        except Exception as e:
            logger.error(f"STT 처리 실패: {str(e)}")
            # 빈 결과 반환 (서버 오류 방지)
            return {
                "transcript": "",
                "speaker_segments": [],
                "duration": 0,
                "speaker_count": 0
            }
    
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
    
    def validate_audio_format(self, audio_content: bytes) -> bool:
        """
        오디오 파일 형식이 유효한지 검증
        
        Args:
            audio_content: 오디오 파일의 바이트 데이터
            
        Returns:
            bool: 유효한 형식이면 True
        """
        try:
            # WebM 파일 시그니처 확인 (간단한 검증)
            if len(audio_content) < 4:
                return False
            
            # WebM 파일은 EBML 헤더로 시작 (0x1A, 0x45, 0xDF, 0xA3)
            webm_signature = b'\x1a\x45\xdf\xa3'
            if audio_content[:4] == webm_signature:
                return True
            
            # 추가적인 오디오 형식 검증 로직을 여기에 추가할 수 있음
            logger.warning("지원하지 않는 오디오 형식입니다")
            return False
            
        except Exception as e:
            logger.error(f"오디오 형식 검증 실패: {str(e)}")
            return False
