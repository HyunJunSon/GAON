from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import os
from langsmith import Client

from .core.config import settings
from .domains.auth.user_router import auth_router

# LangSmith 환경 변수 설정
if settings.langchain_api_key:
    os.environ["LANGCHAIN_TRACING_V2"] = settings.langchain_tracing_v2
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    
    # LangSmith 클라이언트 초기화
    client = Client()

app = FastAPI()

# 설정에서 가져온 프론트엔드 URL 또는 기본값 사용
origins = [settings.frontend_url]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"message": "안녕하세요. 가족의온도를 책임지는 가온 입니다."}


app.include_router(auth_router)
