from app.agent.Cleaner.graph_cleaner import CleanerGraph

def run_cleaner(sample=True):
    """
    Cleaner 모듈 실행 진입점 함수
    """
    cg = CleanerGraph(verbose=True)
    result = cg.run(sample=sample)

    # 후속 단계용 기본 메타데이터 추가
    result_dict = {
        "conv_id": "C001",
        "conversation_df": result.cleaned_df if hasattr(result, "cleaned_df") else None,
        "user_id": "201",  # 샘플 사용자 ID
    }

    print("✅ [CleanerGraph] 실행 완료")
    return result_dict


if __name__ == "__main__":
    print("단독 실행 모드")
    output = run_cleaner(sample=True)
    print(output)
