# app/agent/Analysis/run_analysis.py
from app.agent.Analysis.graph_analysis import AnalysisGraph
import pprint
import pandas as pd

# ---------------------------------------------
# ✅ 외부에서 import 가능하도록 함수로 분리
# ---------------------------------------------
def run_analysis(conv_id="C001", user_id="201", conversation_df=None):
    """
    Analysis 모듈 실행 함수
    - main_run.py 에서 Cleaner 단계 결과를 전달받아 실행됨
    """
    print("\n[AnalysisGraph] 실행 시작")
    print("=" * 60)

    # conversation_df가 없을 경우 샘플 데이터를 로드
    if conversation_df is None:
        conversation_df = pd.DataFrame([
            {"speaker": "201", "text": "오늘 하루 어땠어?", "timestamp": "2025-11-04 18:10:00"},
            {"speaker": "202", "text": "그냥 평범했어. 회사 일 많았어.", "timestamp": "2025-11-04 18:11:10"},
            {"speaker": "201", "text": "요즘 피곤해 보이네. 괜찮아?", "timestamp": "2025-11-04 18:12:00"},
        ])

    # AnalysisGraph 실행
    graph = AnalysisGraph(verbose=True)
    result = graph.run(conversation_df=conversation_df, user_id=user_id, conv_id=conv_id)

    print("\n✅ [AnalysisGraph] 파이프라인 완료")
    print("=" * 60)
    pprint.pprint(result)

    # main_run.py로 반환
    return result


# ---------------------------------------------
# ✅ 단독 실행 지원 (기존 코드 유지)
# ---------------------------------------------
def main():
    result = run_analysis()
    return result


if __name__ == "__main__":
    main()
