# app/agent/QA/run_qa.py
from app.agent.QA.graph_qa import QAGraph
import pandas as pd
import pprint

def main():
    print("\n[QAGraph] 실행 시작")
    print("=" * 60)

    # ✅ AnalysisGraph에서 결과를 불러온다고 가정
    conversation_df = pd.DataFrame([
        {"speaker": "201", "text": "오늘 하루 어땠어?", "timestamp": "2025-11-04 18:10:00"},
        {"speaker": "202", "text": "그냥 평범했어. 회사 일 많았어.", "timestamp": "2025-11-04 18:11:10"},
    ])
    analysis_result = {
        "summary": "따뜻한 가족 간 대화",
        "style_analysis": {"emotion": "긍정적", "tone": "편안함"},
        "score": 0.62,  # 일부러 낮게 설정해서 ReAnalyzer 트리거
    }

    graph = QAGraph(verbose=True)
    result = graph.run(
        conversation_df=conversation_df,
        analysis_result=analysis_result,
        user_id="201",
        conv_id="C001",
    )

    print("\n✅ [QAGraph] 파이프라인 완료")
    print("=" * 60)
    pprint.pprint(result)

if __name__ == "__main__":
    main()
