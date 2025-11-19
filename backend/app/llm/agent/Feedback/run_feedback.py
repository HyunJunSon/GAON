# backend/app/llm/agent/Feedback/run_feedback.py
# -*- coding: utf-8 -*-

from typing import Dict, Any, Optional
import pandas as pd
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.llm.agent.Feedback.graph_feedback import FeedbackGraph


def run_feedback(
    conv_id: str,
    id: int,
    conversation_df: pd.DataFrame,
    analysis_id: Optional[str] = None,   # ✅ 어떤 분석 결과랑 묶을지 명시
    db: Optional[Session] = None,        # (옵션) 이미 열린 세션 재사용 가능
    verbose: bool = True,
) -> Dict[str, Any]:
    if verbose:
        print("\n" + "=" * 60)
        print("💡 [Feedback] 실행 시작")
        print("=" * 60)

    if not conv_id:
        raise ValueError("❌ conv_id가 필요합니다!")
    if not id:
        raise ValueError("❌ id가 필요합니다!")
    if conversation_df is None or conversation_df.empty:
        raise ValueError("❌ conversation_df가 비어 있습니다!")

    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        graph = FeedbackGraph(verbose=verbose)
        result = graph.run(
            db=db,
            conv_id=conv_id,
            id=id,
            analysis_id=analysis_id,        # ✅ 그래프 state 로 전달
            conversation_df=conversation_df,
        )

        if verbose:
            print("\n" + "=" * 60)
            print("✅ [Feedback] 실행 완료")
            print("=" * 60)
            print(f"\n📌 feedback 앞 200자:\n{(result.get('advice_text') or '')[:200]}...\n")

        return result

    finally:
        if owns_session:
            db.close()