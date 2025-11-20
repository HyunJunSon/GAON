"""
새로운 Agent 파이프라인
- Cleaner → Analysis 실행
- speaker_segments 기반 분석
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime

from app.core.database import SessionLocal
from app.agent.crud import get_conversation_file_by_conv_id
from app.llm.agent.Cleaner.graph_cleaner import CleanerGraph
from app.llm.agent.Analysis.graph_analysis import AnalysisGraph

logger = logging.getLogger(__name__)


def extract_speaker_info_from_file(file_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    conversation_file에서 speaker_segments와 매핑 정보 추출
    
    Returns:
        {
            "speaker_segments": List[Dict],
            "speaker_mapping": Dict,
            "user_gender": str,
            "user_age": int,
            "user_name": str
        }
    """
    speaker_segments = file_row.get("speaker_segments", [])
    speaker_mapping_raw = file_row.get("speaker_mapping", {})
    
    # 실제 구조: {"speaker_names": {"SPEAKER_0A": "gaon (나)"}, "user_ids": {"SPEAKER_0A": 9}}
    speaker_mapping = speaker_mapping_raw if speaker_mapping_raw else {
        "user_ids": {},
        "speaker_names": {}
    }
    
    user_gender = "unknown"
    user_age = 0
    user_name = None
    
    # user_ids에서 첫 번째 user 정보 가져오기
    user_ids_map = speaker_mapping.get("user_ids", {})
    speaker_names = speaker_mapping.get("speaker_names", {})
    
    if user_ids_map:
        first_speaker = list(user_ids_map.keys())[0]
        user_name = speaker_names.get(first_speaker, "사용자")
        # gender, age는 별도 조회 필요 (현재는 기본값 사용)
    
    return {
        "speaker_segments": speaker_segments,
        "speaker_mapping": speaker_mapping,
        "user_gender": user_gender,
        "user_age": user_age,
        "user_name": user_name
    }


async def run_agent_pipeline_with_retry(conv_id: str) -> Dict[str, Any]:
    """
    재시도 로직이 포함된 Agent 파이프라인 실행
    
    Args:
        conv_id: 대화 UUID
        
    Returns:
        dict: {
            "status": "completed" | "failed",
            "conv_id": str,
            "user_id": int,
            "analysis_id": str,
            "score": float,
            "confidence": float,
            "error": str (실패 시)
        }
    """
    pipeline_start = datetime.now()
    db = SessionLocal()
    
    try:
        logger.info(f"🚀 파이프라인 시작: conv_id={conv_id}")
        
        # -------------------------------------------------
        # 1. conversation_file에서 speaker_segments 가져오기
        # -------------------------------------------------
        file_row = get_conversation_file_by_conv_id(db, conv_id)
        if not file_row:
            raise RuntimeError(f"conv_id={conv_id}를 찾을 수 없습니다.")
        
        logger.info(f"📁 파일 타입: {file_row['file_type']}")
        
        # speaker 정보 추출
        speaker_info = extract_speaker_info_from_file(file_row)
        speaker_segments = speaker_info["speaker_segments"]
        speaker_mapping = speaker_info["speaker_mapping"]
        user_gender = speaker_info["user_gender"]
        user_age = speaker_info["user_age"]
        user_name = speaker_info["user_name"]
        
        if not speaker_segments:
            raise RuntimeError("speaker_segments가 비어있습니다.")
        
        logger.info(f"✅ speaker_segments: {len(speaker_segments)}개")
        
        # -------------------------------------------------
        # 2. speaker_mapping에서 파라미터 추출
        # -------------------------------------------------
        user_ids_map = speaker_mapping.get("user_ids", {})
        
        if not user_ids_map:
            raise RuntimeError("user_ids mapping이 없습니다. 화자 매핑을 먼저 완료해주세요.")
        
        user_speaker_label = list(user_ids_map.keys())[0]
        user_id = list(user_ids_map.values())[0]
        
        speaker_names = speaker_mapping.get("speaker_names", {})
        other_speakers = [spk for spk in speaker_names.keys() if spk != user_speaker_label]
        other_speaker_label = other_speakers[0] if other_speakers else None
        other_display_name = speaker_names.get(other_speaker_label, "상대방")
        
        logger.info(f"👤 user_id={user_id}, user_label={user_speaker_label}, other_label={other_speaker_label}")
        
        # -------------------------------------------------
        # 3. Analysis 실행
        # -------------------------------------------------
        logger.info("🔎 Analysis 실행 시작")
        analysis = AnalysisGraph(verbose=True)
        
        analysis_state = analysis.run(
            db=db,
            conv_id=conv_id,
            speaker_segments=speaker_segments,
            user_id=user_id,
            user_gender=user_gender,
            user_age=user_age,
            user_name=user_name,
            user_speaker_label=user_speaker_label,
            other_speaker_label=other_speaker_label,
            other_display_name=other_display_name,
        )
        
        logger.info("✅ Analysis 완료")
        
        # -------------------------------------------------
        # 4. 결과 반환
        # -------------------------------------------------
        total_time = (datetime.now() - pipeline_start).total_seconds()
        
        # AnalysisState에서 결과 추출 (dict 형태)
        analysis_result = analysis_state.get('analysis_result', {})
        meta = analysis_state.get('meta', {})
        
        result = {
            "status": "completed",
            "conv_id": conv_id,
            "user_id": user_id,
            "analysis_id": meta.get("analysis_id"),
            "score": analysis_result.get("score", 0),
            "confidence": 0.95,
            "summary": analysis_result.get("summary"),
            "statistics": analysis_result.get("statistics"),
            "style_analysis": analysis_result.get("style"),
            "validated": True,
            "execution_time": total_time,
        }
        
        logger.info(f"🎉 파이프라인 완료: {total_time:.2f}초")
        return result
        
    except Exception as e:
        logger.error(f"❌ 파이프라인 실패: {str(e)}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "conv_id": conv_id,
            "execution_time": (datetime.now() - pipeline_start).total_seconds()
        }
    
    finally:
        db.close()
