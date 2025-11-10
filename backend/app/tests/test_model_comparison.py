import os
import time
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from langsmith import traceable
from app.core.config import settings

# LangSmith 환경변수 설정
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project

# 테스트 프롬프트들
TEST_PROMPTS = [
    "가족 간의 소통 문제를 해결하는 방법을 3가지 제시해주세요.",
    "부모와 자녀 간의 대화에서 자주 발생하는 갈등 상황과 해결책을 설명해주세요.",
    "효과적인 경청의 기술에 대해 설명하고 실제 적용 방법을 알려주세요.",
    "가족 내에서 감정 표현을 어려워하는 사람들을 위한 조언을 해주세요."
]

@traceable(name="gpt4_analysis")
def test_gpt4(prompt: str):
    """GPT-4 모델 테스트"""
    model = ChatOpenAI(
        model="gpt-4o",
        api_key=settings.openai_api_key,
        temperature=0.7
    )
    
    start_time = time.time()
    response = model.invoke([HumanMessage(content=prompt)])
    end_time = time.time()
    
    return {
        "model": "GPT-4o",
        "response": response.content,
        "response_time": round(end_time - start_time, 2),
        "response_length": len(response.content)
    }

@traceable(name="gpt35_analysis")
def test_gpt35(prompt: str):
    """GPT-3.5 모델 테스트"""
    model = ChatOpenAI(
        model="gpt-3.5-turbo",
        api_key=settings.openai_api_key,
        temperature=0.7
    )
    
    start_time = time.time()
    response = model.invoke([HumanMessage(content=prompt)])
    end_time = time.time()
    
    return {
        "model": "GPT-3.5-turbo",
        "response": response.content,
        "response_time": round(end_time - start_time, 2),
        "response_length": len(response.content)
    }

@traceable(name="gemini_pro_analysis")
def test_gemini_pro(prompt: str):
    """Gemini Pro 모델 테스트"""
    model = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro-latest",
        google_api_key=settings.gemini_api_key,
        temperature=0.7
    )
    
    start_time = time.time()
    response = model.invoke([HumanMessage(content=prompt)])
    end_time = time.time()
    
    return {
        "model": "Gemini-1.5-Pro",
        "response": response.content,
        "response_time": round(end_time - start_time, 2),
        "response_length": len(response.content)
    }

@traceable(name="gemini_flash_analysis")
def test_gemini_flash(prompt: str):
    """Gemini Flash 모델 테스트"""
    model = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash-latest",
        google_api_key=settings.gemini_api_key,
        temperature=0.7
    )
    
    start_time = time.time()
    response = model.invoke([HumanMessage(content=prompt)])
    end_time = time.time()
    
    return {
        "model": "Gemini-1.5-Flash",
        "response": response.content,
        "response_time": round(end_time - start_time, 2),
        "response_length": len(response.content)
    }

@traceable(name="model_comparison_test")
def run_model_comparison():
    """모든 모델 비교 테스트 실행"""
    print("🚀 모델 성능 비교 테스트 시작...")
    print(f"📊 LangSmith 프로젝트: {settings.langchain_project}")
    
    models = [test_gpt4, test_gpt35, test_gemini_pro, test_gemini_flash]
    
    for i, prompt in enumerate(TEST_PROMPTS, 1):
        print(f"\n📝 테스트 {i}: {prompt[:50]}...")
        
        for model_func in models:
            try:
                result = model_func(prompt)
                print(f"✅ {result['model']}: {result['response_time']}초, {result['response_length']}자")
            except Exception as e:
                print(f"❌ {model_func.__name__}: 오류 - {str(e)}")
    
    print(f"\n🎯 LangSmith 대시보드에서 결과 확인: https://smith.langchain.com/")
    print(f"📈 프로젝트: {settings.langchain_project}")

if __name__ == "__main__":
    run_model_comparison()
