import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from app.core.config import settings

# 환경 변수 설정 (main.py와 동일)
if settings.langchain_api_key:
    os.environ["LANGCHAIN_TRACING_V2"] = settings.langchain_tracing_v2
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key

def test_langsmith_tracing():
    """LangSmith 추적 테스트"""
    print("LangSmith 테스트 시작...")
    
    # Gemini 모델 초기화
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.gemini_api_key
    )
    
    # 테스트 메시지
    message = HumanMessage(content="안녕하세요! Gaon 프로젝트 테스트입니다. Gaon이 뭔지 궁금하신가요?")
    
    # LLM 호출 (자동으로 LangSmith에 추적됨)
    response = llm.invoke([message])
    
    print(f"응답: {response.content}")
    print("LangSmith 대시보드에서 추적 결과를 확인하세요!")
    print(f"프로젝트: {settings.langchain_project}")

if __name__ == "__main__":
    test_langsmith_tracing()
