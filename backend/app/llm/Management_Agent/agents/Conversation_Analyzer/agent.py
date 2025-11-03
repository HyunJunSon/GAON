"""
Conversation Analyzer Agent

이 에이전트는 conversation 테이블의 데이터를 분석하여
사용자별 대화 특징을 추출하고 JSON 형태로 출력하는 역할을 합니다.

주요 기능:
1. 대화 데이터 분석
2. OpenAI를 사용한 심층 분석
3. 사용자별 프로필 생성
4. 결과를 JSON으로 저장

입력: conversation 테이블 데이터
출력: conversation_analysis.json
"""

import pandas as pd
import json
from datetime import datetime
from collections import Counter
from openai import OpenAI
from typing import Dict, Any

from app.core.config import settings
from app.core.database import SessionLocal

class ConversationAnalyzer:
    def __init__(self):
        """ConversationAnalyzer 초기화"""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.db = SessionLocal()

    def analyze_conversation_style(self, text: str) -> Dict[str, Any]:
        """OpenAI를 사용하여 대화 스타일 분석"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": """다음 대화에서 화자의 특징을 분석해주세요:
                    1. 말투 특징 (존댓말/반말, 어미 사용 등)
                    2. 대화 성향 (적극성/소극성, 감정 표현 정도)
                    3. 주요 관심사
                    JSON 형식으로 응답해주세요."""},
                    {"role": "user", "content": text}
                ]
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"대화 스타일 분석 중 오류 발생: {str(e)}")
            return {
                "speaking_style": "분석 실패",
                "conversation_tendency": "분석 실패",
                "main_interests": []
            }

    def calculate_statistics(self, text: str) -> Dict[str, Any]:
        """대화 통계 계산"""
        words = text.split()
        sentences = text.split('.')
        
        return {
            "word_count": len(words),
            "avg_sentence_length": len(words) / len(sentences) if sentences else 0,
            "unique_words": len(set(words)),
            "top_words": [word for word, _ in Counter(words).most_common(5)]
        }

    def analyze_conversations(self) -> Dict[str, Any]:
        """conversation 테이블의 모든 대화 분석"""
        try:
            # 데이터 읽기
            query = "SELECT * FROM conversation"
            conv_df = pd.read_sql(query, self.db.bind)

            analysis_results = {}
            
            # 사용자별 분석
            for user_id, group in conv_df.groupby("user_id"):
                # 모든 대화 내용 합치기
                all_content = "\n".join(group["content"].tolist())
                
                # 통계 계산
                stats = self.calculate_statistics(all_content)
                
                # 대화 스타일 분석
                style_analysis = self.analyze_conversation_style(all_content)
                
                # 결과 조합
                # handle optional columns gracefully
                emotions = group["emotion"].value_counts().to_dict() if "emotion" in group.columns else {}
                last_conv = str(group["create_date"].max()) if "create_date" in group.columns else None

                analysis_results[str(user_id)] = {
                    "user_id": int(user_id),
                    "conversation_count": len(group),
                    "statistics": stats,
                    "style_analysis": style_analysis,
                    "emotions": emotions,
                    "last_conversation": last_conv,
                    "analysis_date": datetime.now().isoformat()
                }

            return analysis_results

        except Exception as e:
            print(f"분석 중 오류 발생: {str(e)}")
            raise

    def save_analysis(self, analysis: Dict[str, Any]):
        """분석 결과를 JSON 파일로 저장"""
        try:
            output_path = "conversation_analysis.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2)
            print(f"[Conversation Analyzer] 분석 결과 저장 완료: {output_path}")
        except Exception as e:
            print(f"결과 저장 중 오류 발생: {str(e)}")
            raise

    def run(self):
        """전체 분석 프로세스 실행"""
        try:
            print("[Conversation Analyzer] 분석 시작")
            analysis_results = self.analyze_conversations()
            self.save_analysis(analysis_results)
            print("[Conversation Analyzer] 분석 완료")
            return analysis_results
        except Exception as e:
            print(f"실행 중 오류 발생: {str(e)}")
            raise
        finally:
            self.db.close()

if __name__ == "__main__":
    analyzer = ConversationAnalyzer()
    analyzer.run()