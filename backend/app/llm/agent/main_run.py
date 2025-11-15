# app/main_run.py
"""
✅ 전체 에이전트(Cleaner → Analysis → QA) 파이프라인 실행 파일

각 Agent의 run_*.py 모듈을 순차적으로 호출하며,
마지막 결과를 DB에 저장합니다.

"""

import os
import sys
from pprint import pprint

# 루트 경로 인식
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# 테스트 DB 환경 활성화 (운영 시 false)
os.environ["USE_TEST_DB"] = "true"
# ----------------------------------------

# ----------------------------------------
# Agent 모듈 임포트
# ----------------------------------------
from app.llm.agent.Cleaner.run_cleaner import run_cleaner
from app.llm.agent.Analysis.run_analysis import run_analysis
from app.llm.agent.QA.run_qa import run_qa

# ----------------------------------------
# 메인 실행 로직
# ----------------------------------------
def main():
    print("\n🚀 [GAON MAIN PIPELINE] 실행 시작")
    print("=" * 60)

    # =========================================
    # 1️⃣ Cleaner 실행
    # =========================================
    print("\n[1️⃣ CLEANER] 데이터 정제 단계 시작")
    
    # 🔧 수정: sample 파라미터 제거
    # run_cleaner()는 자동으로 최근 대화 조회
    cleaner_result = run_cleaner()
    
    print("\n📊 [Cleaner 결과]")
    print("-" * 60)
    pprint(cleaner_result)
    
    # ✅ Cleaner 결과 추출
    conv_id = cleaner_result.get("conv_id")
    id = cleaner_result.get("id")
    cleaned_df = cleaner_result.get("cleaned_df")  
    validated = cleaner_result.get("validated", False)
    
    # ✅ 필수 데이터 검증
    if not conv_id:
        raise ValueError("❌ Cleaner 단계에서 conv_id가 반환되지 않았습니다.")
    
    if not id:
        raise ValueError("❌ Cleaner 단계에서 id가 반환되지 않았습니다.")
    
    if cleaned_df is None or cleaned_df.empty:
        raise ValueError("❌ Cleaner 단계에서 cleaned_df가 반환되지 않았습니다.")
    
    if not validated:
        raise ValueError("❌ Cleaner 검증 실패: 분석 불가능한 대화입니다.")
    
    print(f"\n✅ Cleaner 완료: conv_id={conv_id}, id={id}, 발화 수={len(cleaned_df)}")

    # =========================================
    # 2️⃣ Analysis 실행
    # =========================================
    print("\n[2️⃣ ANALYSIS] 분석 단계 시작")
    
    analysis_result = run_analysis(
        conv_id=conv_id,
        id=id,
        conversation_df=cleaned_df  
    )
    
    print("\n📊 [Analysis 결과]")
    print("-" * 60)
    pprint(analysis_result)
    
    # ✅ Analysis 결과 검증
    if not analysis_result.get("analysis_id"):
        raise ValueError("❌ Analysis 단계에서 analysis_id가 반환되지 않았습니다.")
    
    print(f"\n✅ Analysis 완료: analysis_id={analysis_result.get('analysis_id')}")

    # =========================================
    # 3️⃣ QA 실행
    # =========================================
    print("\n[3️⃣ QA] 품질 평가 단계 시작")
    
    # 🔧 수정: 파라미터 구조 수정
    qa_result = run_qa(
        analysis_result=analysis_result["analysis_result"],  
        conversation_df=cleaned_df,  
        id=id,
        conv_id=conv_id  
    )
    
    print("\n📊 [QA 결과]")
    print("-" * 60)
    pprint(qa_result)
    
    print(f"\n✅ QA 완료: confidence={qa_result.get('confidence', 0):.2f}")

    # =========================================
    # ✅ 최종 완료
    # =========================================
    print("\n" + "=" * 60)
    print("✅ [GAON PIPELINE COMPLETED] 전체 파이프라인 완료")
    print("=" * 60)
    
    # ✅ 최종 결과 요약
    print("\n📋 [최종 결과 요약]")
    print(f"   대화 ID: {conv_id}")
    print(f"   사용자 ID: {id}")
    print(f"   분석 ID: {analysis_result.get('analysis_id')}")
    print(f"   말하기 점수: {analysis_result.get('analysis_result', {}).get('score', 0):.2f}")
    print(f"   신뢰도 점수: {qa_result.get('confidence', 0):.2f}")
    print(f"   QA 상태: {qa_result.get('status', 'unknown')}")
    
    return {
        "conv_id": conv_id,
        "id": id,
        "analysis_id": analysis_result.get("analysis_id"),
        "score": analysis_result.get("analysis_result", {}).get("score", 0),
        "confidence": qa_result.get("confidence", 0),
        "status": "completed"
    }


if __name__ == "__main__":
    main()