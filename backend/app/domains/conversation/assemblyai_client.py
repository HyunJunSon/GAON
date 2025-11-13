import logging
import requests
import time
from typing import Dict, Any, List
import base64
from app.core.config import settings

logger = logging.getLogger(__name__)


class AssemblyAIClient:
    """AssemblyAI API 클라이언트"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'assemblyai_api_key', '')
        self.base_url = "https://api.assemblyai.com/v2"
        self.headers = {
            "authorization": self.api_key,
            "content-type": "application/json"
        }
    
    def transcribe_with_speakers(self, audio_content: bytes, filename: str) -> Dict[str, Any]:
        """
        AssemblyAI로 화자분리 포함 음성 인식
        """
        try:
            logger.info(f"AssemblyAI 처리 시작: {filename}")
            
            # 1. 오디오 파일 업로드
            upload_url = self._upload_audio(audio_content)
            
            # 2. 전사 요청 (화자분리 활성화)
            transcript_id = self._request_transcription(upload_url)
            
            # 3. 결과 대기 및 가져오기
            result = self._get_transcription_result(transcript_id)
            
            logger.info(f"AssemblyAI 처리 완료: {len(result['segments'])}개 세그먼트, {result['speaker_count']}명 화자")
            return result
            
        except Exception as e:
            logger.error(f"AssemblyAI 오류: {e}")
            raise Exception(f"AssemblyAI 음성 인식 실패: {e}")
    
    def _upload_audio(self, audio_content: bytes) -> str:
        """오디오 파일을 AssemblyAI에 업로드"""
        upload_response = requests.post(
            f"{self.base_url}/upload",
            headers={"authorization": self.api_key},
            data=audio_content
        )
        upload_response.raise_for_status()
        return upload_response.json()["upload_url"]
    
    def _request_transcription(self, audio_url: str) -> str:
        """전사 요청 (화자분리 포함)"""
        data = {
            "audio_url": audio_url,
            "speaker_labels": True,  # 화자분리 활성화
            "speakers_expected": None,  # 자동 감지
            "language_code": "ko"  # 한국어
        }
        
        response = requests.post(
            f"{self.base_url}/transcript",
            json=data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()["id"]
    
    def _get_transcription_result(self, transcript_id: str) -> Dict[str, Any]:
        """전사 결과 가져오기 (폴링)"""
        while True:
            response = requests.get(
                f"{self.base_url}/transcript/{transcript_id}",
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            
            if result["status"] == "completed":
                return self._parse_result(result)
            elif result["status"] == "error":
                raise Exception(f"AssemblyAI 전사 실패: {result.get('error')}")
            
            time.sleep(2)  # 2초 대기 후 재시도
    
    def _parse_result(self, raw_result: Dict) -> Dict[str, Any]:
        """AssemblyAI 결과를 표준 형식으로 변환"""
        segments = []
        speakers = set()
        
        for utterance in raw_result.get("utterances", []):
            speaker = f"SPEAKER_{str(utterance['speaker']).zfill(2)}"
            speakers.add(speaker)
            
            segments.append({
                "start": utterance["start"] / 1000.0,  # ms to seconds
                "end": utterance["end"] / 1000.0,
                "text": utterance["text"].strip(),
                "speaker": speaker,
                "confidence": utterance.get("confidence", 0.8)
            })
        
        return {
            "segments": segments,
            "speaker_count": len(speakers),
            "full_text": raw_result.get("text", ""),
            "processing_method": "assemblyai"
        }
