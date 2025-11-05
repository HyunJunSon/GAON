# app/agent/Analysis/run_analysis.py
from app.agent.Analysis.graph_analysis import AnalysisGraph
import pprint

def main():
    print("\n[AnalysisGraph] 실행 시작")
    print("=" * 60)

    # ✅ CleanerGraph 에서 저장된 conversation_df를 로드했다고 가정
    import pandas as pd
    conversation_df = pd.DataFrame([
        {"speaker": "201", "text": "오늘 하루 어땠어?", "timestamp": "2025-11-04 18:10:00"},
        {"speaker": "202", "text": "그냥 평범했어. 회사 일 많았어.", "timestamp": "2025-11-04 18:11:10"},
        {"speaker": "201", "text": "요즘 피곤해 보이네. 괜찮아?", "timestamp": "2025-11-04 18:12:00"},
    ])

    graph = AnalysisGraph(verbose=True)
    result = graph.run(conversation_df=conversation_df, user_id="201", conv_id="C001")

    print("\n✅ [AnalysisGraph] 파이프라인 완료")
    print("=" * 60)
    pprint.pprint(result)

if __name__ == "__main__":
    main()
