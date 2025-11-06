# app/main_run.py
"""
전체 에이전트(Cleaner → Analysis → QA) 파이프라인 실행 파일
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
from app.agent.Cleaner.run_cleaner import run_cleaner
from app.agent.Analysis.run_analysis import run_analysis
from app.agent.QA.run_qa import run_qa

# ----------------------------------------
# 메인 실행 로직
# ----------------------------------------
def main():
    print("\n🚀 [GAON MAIN PIPELINE] 실행 시작")
    print("=" * 60)

    # 1️⃣ Cleaner 실행
    print("\n[1️⃣ CLEANER] 데이터 정제 단계 시작")
    cleaner_result = run_cleaner(sample=True)
    pprint(cleaner_result)

    conv_id = cleaner_result.get("conv_id", "C001")
    conversation_df = cleaner_result.get("conversation_df")
    if conversation_df is None:
        raise ValueError("Cleaner 단계에서 conversation_df가 반환되지 않았습니다.")
    user_id = cleaner_result.get("user_id", "201")

    # 2️⃣ Analysis 실행
    print("\n[2️⃣ ANALYSIS] 분석 단계 시작")
    analysis_result = run_analysis(conv_id=conv_id, user_id=user_id, conversation_df=conversation_df)
    pprint(analysis_result)

    # 3️⃣ QA 실행
    print("\n[3️⃣ QA] 품질 평가 단계 시작")
    qa_result = run_qa(analysis_result=analysis_result, conversation_df=conversation_df, user_id=user_id)
    pprint(qa_result)

    print("\n✅ [GAON PIPELINE COMPLETED] 전체 파이프라인 완료")
    print("=" * 60)

if __name__ == "__main__":
    main()
