# app/agent/QA/run_qa.py
from app.agent.QA.graph_qa import QAGraph
import pandas as pd
import pprint


# ---------------------------------------------
# ✅ 외부에서 import 가능하도록 함수 추가
# ---------------------------------------------
def run_qa(analysis_result=None, conversation_df=None, user_id="201", conv_id="C001"):
    """
    QA 모듈 실행 함수
    - main_run.py 에서 Analysis 단계 결과를 전달받아 실행됨
    """
    print("\n[QAGraph] 실행 시작")
    print("=" * 60)

    # Analysis 단계 결과가 없을 경우 기본 샘플 세팅
    if analysis_result is None:
        analysis_result = {
            "summary": "따뜻한 가족 간 대화",
            "style_analysis": {"emotion": "긍정적", "tone": "편안함"},
            "score": 0.62,  # 일부러 낮게 설정해서 ReAnalyzer 트리거
        }

    if conversation_df is None:
        conversation_df = pd.DataFrame([
            {"speaker": "201", "text": "오늘 하루 어땠어?", "timestamp": "2025-11-04 18:10:00"},
            {"speaker": "202", "text": "그냥 평범했어. 회사 일 많았어.", "timestamp": "2025-11-04 18:11:10"},
        ])

    # QAGraph 실행
    graph = QAGraph(verbose=True)
    result = graph.run(
        conversation_df=conversation_df,
        analysis_result=analysis_result,
        user_id=user_id,
        conv_id=conv_id,
    )

    print("\n✅ [QAGraph] 파이프라인 완료")
    print("=" * 60)
    pprint.pprint(result)

    # main_run.py에서 다음 단계로 전달할 수 있게 반환
    return result


# ---------------------------------------------
# ✅ 단독 실행 지원 (기존 코드 유지)
# ---------------------------------------------
def main():
    """
    단독 실행 시 QA 단위 테스트용으로 동작
    """
    result = run_qa()
    return result


if __name__ == "__main__":
    main()
