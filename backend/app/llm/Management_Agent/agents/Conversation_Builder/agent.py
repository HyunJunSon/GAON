"""
Conversation Builder Agent

이 에이전트는 test_raw_conversation 테이블의 원시 대화 데이터를 가져와서
정제된 형태로 conversation 테이블에 변환하여 저장하는 역할을 합니다.

주요 기능:
1. Raw 데이터 추출 및 전처리
2. OpenAI를 사용한 대화 내용 요약
3. 감정 분석 및 태깅
4. 정제된 데이터를 conversation 테이블에 저장

입력: test_raw_conversation 테이블 데이터
출력: conversation 테이블 데이터
"""

import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from openai import OpenAI
from typing import List, Dict, Any

from app.core.config import settings
from app.core.database import SessionLocal

class ConversationBuilder:
    def __init__(self):
        """ConversationBuilder 초기화"""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.db = SessionLocal()

    def summarize_conversation(self, text: str) -> str:
        """OpenAI를 사용하여 대화 내용을 요약"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "대화 내용을 간단하게 요약해주세요."},
                    {"role": "user", "content": text}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"요약 중 오류 발생: {str(e)}")
            return text

    def analyze_emotion(self, text: str) -> str:
        """OpenAI를 사용하여 대화의 주된 감정 분석"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "다음 대화의 주된 감정을 'happy', 'sad', 'neutral', 'angry' 중 하나로 분류해주세요."},
                    {"role": "user", "content": text}
                ]
            )
            return response.choices[0].message.content.strip().lower()
        except Exception as e:
            print(f"감정 분석 중 오류 발생: {str(e)}")
            return "neutral"

    def process_raw_conversations(self) -> pd.DataFrame:
        """원시 대화 데이터 처리"""
        try:
            # Raw 데이터 읽기
            query = "SELECT * FROM test_raw_conversation ORDER BY user_id, timestamp"
            raw_df = pd.read_sql(query, self.db.bind)

            # 사용자별로 그룹화하여 처리
            processed_data = []
            for user_id, group in raw_df.groupby("user_id"):
                # 대화 텍스트 합치기
                full_text = "\n".join(group["text"].tolist())
                
                # 대화 요약
                summary = self.summarize_conversation(full_text)
                
                # 주된 감정 분석
                main_emotion = self.analyze_emotion(full_text)
                
                processed_data.append({
                    "user_id": user_id,
                    "title": f"User_{user_id}_Session_{datetime.now().strftime('%Y%m%d')}",
                    "content": summary,
                    "create_date": datetime.now(),
                    "family_id": None
                })

            return pd.DataFrame(processed_data)

        except Exception as e:
            print(f"데이터 처리 중 오류 발생: {str(e)}")
            raise

    def save_to_conversation(self, df: pd.DataFrame):
        """처리된 데이터를 conversation 테이블에 저장"""
        try:
            df.to_sql("conversation", self.db.bind, if_exists="append", index=False)
            print("[Conversation Builder] 데이터 저장 완료")
        except Exception as e:
            print(f"데이터 저장 중 오류 발생: {str(e)}")
            raise

    def run(self):
        """전체 처리 프로세스 실행"""
        try:
            print("[Conversation Builder] 처리 시작")
            processed_df = self.process_raw_conversations()
            self.save_to_conversation(processed_df)
            print("[Conversation Builder] 처리 완료")
            return processed_df
        except Exception as e:
            print(f"처리 중 오류 발생: {str(e)}")
            raise
        finally:
            self.db.close()

if __name__ == "__main__":
    builder = ConversationBuilder()
    builder.run()