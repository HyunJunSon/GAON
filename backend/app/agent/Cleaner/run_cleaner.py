from .graph_cleaner import CleanerGraph
import pprint

def main():
    cg = CleanerGraph(verbose=True)
    res = cg.run()

    # ✅ 결과 확인
    print("\n=== ✅ 최종 상태 ===")
    pprint.pprint(res.__dict__)

    # conversation_df 출력
    conv_df = res.meta.get("conversation_df")
    if conv_df is not None:
        try:
            print("\n=== 💾 conversation_df ===")
            print(conv_df.to_string(index=False))
        except Exception:
            print(conv_df)

if __name__ == "__main__":
    main()
