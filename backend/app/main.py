from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from .core.config import settings
from .domains.auth.user_router import auth_router
from .domains.conversation.router import router as conversation_router

# 모든 모델 import (SQLAlchemy 관계 설정을 위해 필요)
from .domains.auth.user_models import User
from .domains.conversation.models import Conversation
from .domains.conversation.file_models import ConversationFile
from .domains.family.models import Family

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
app.include_router(conversation_router)
