"""
PostgreSQL 벡터 DB 통합 모듈
pgvector 확장을 사용하여 문서 임베딩을 저장하고 검색
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy import create_engine, Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from pgvector.sqlalchemy import Vector

# 기존 데이터베이스 설정 가져오기
from app.core.config import settings

# 로깅 및 예외 처리 모듈 가져오기
from ..logger import rag_logger
from ..exception import VectorDBException as RAGVectorDBException, EmbeddingException as RAGEmbeddingException

logger = rag_logger

# 베이스 클래스 생성
Base = declarative_base()


class IdealAnswer(Base):
    """
    이상적인 답변을 저장하는 테이블 모델
    """
    __tablename__ = 'ideal_answer'
    
    # 모범답안ID
    idea_id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # 원문
    source = Column(Text, nullable=False)
    
    # 임베딩 (pgvector)
    embedding = Column(Vector(settings.embedding_dimension))  # 설정에서 임베딩 차원 가져오기
    
    # 생성일
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 분석결과ID (외래키 가능)
    analysisID = Column('analysisid', PostgreSQLUUID(as_uuid=True), nullable=True)


class VectorDBManager:
    """
    PostgreSQL 벡터 데이터베이스 매니저
    임베딩 저장, 검색, 관리 기능 제공
    """
    
    def __init__(self, connection_string: str = None):
        """
        VectorDBManager 초기화
        
        Args:
            connection_string: PostgreSQL 연결 문자열 (선택사항, 기본값은 설정에서 가져옴)
        """
        # 설정에서 연결 정보 가져오기
        if connection_string is None:
            connection_string = settings.database_url or f"postgresql+psycopg2://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
            
        # pgvector 확장을 고려하여 엔진 생성
        self.engine = create_engine(connection_string)
        
        # 세션 생성
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # 테이블 생성 (존재하지 않는 경우)
        Base.metadata.create_all(bind=self.engine)
        
        logger.info("벡터 데이터베이스 매니저 초기화 완료")
    
    def get_session(self) -> Session:
        """
        데이터베이스 세션을 가져옵니다.
        
        Returns:
            데이터베이스 세션
        """
        return self.SessionLocal()
    
    def store_embedding(self, 
                       source: str, 
                       embedding: List[float], 
                       analysis_id: Optional[UUID] = None) -> UUID:
        """
        임베딩을 데이터베이스에 저장합니다.
        
        Args:
            source: 원본 텍스트
            embedding: 임베딩 벡터
            analysis_id: 분석 결과 ID (선택사항)
            
        Returns:
            저장된 레코드의 ID
        """
        session = self.get_session()
        
        try:
            # IdealAnswer 객체 생성
            ideal_answer = IdealAnswer(
                source=source,
                embedding=embedding,
                analysisID=analysis_id
            )
            
            # 데이터베이스에 추가 및 커밋
            session.add(ideal_answer)
            session.commit()
            
            logger.info(f"임베딩 저장 완료: {ideal_answer.idea_id}")
            return ideal_answer.idea_id
        except Exception as e:
            session.rollback()
            logger.error(f"임베딩 저장 실패: {str(e)}")
            raise
        finally:
            session.close()
    
    def store_embeddings_batch(self, 
                              sources: List[str], 
                              embeddings: List[List[float]], 
                              analysis_ids: Optional[List[UUID]] = None) -> List[UUID]:
        """
        여러 임베딩을 일괄 저장합니다.
        
        Args:
            sources: 원본 텍스트 목록
            embeddings: 임베딩 벡터 목록
            analysis_ids: 분석 결과 ID 목록 (선택사항)
            
        Returns:
            저장된 레코드의 ID 목록
        """
        if len(sources) != len(embeddings):
            raise ValueError("sources와 embeddings의 길이가 일치하지 않습니다.")
        
        session = self.get_session()
        
        try:
            stored_ids = []
            
            for i, (source, embedding) in enumerate(zip(sources, embeddings)):
                analysis_id = analysis_ids[i] if analysis_ids and i < len(analysis_ids) else None
                
                ideal_answer = IdealAnswer(
                    source=source,
                    embedding=embedding,
                    analysisID=analysis_id
                )
                
                session.add(ideal_answer)
                stored_ids.append(ideal_answer.idea_id)
            
            session.commit()
            
            logger.info(f"{len(stored_ids)}개 임베딩 일괄 저장 완료")
            return stored_ids
        except Exception as e:
            session.rollback()
            logger.error(f"임베딩 일괄 저장 실패: {str(e)}")
            raise
        finally:
            session.close()
    
    def find_similar(self, 
                     query_embedding: List[float], 
                     top_k: int = 5,
                     threshold: float = 0.5) -> List[Tuple[str, float, UUID]]:
        """
        유사한 임베딩을 검색합니다.
        
        Args:
            query_embedding: 쿼리 임베딩
            top_k: 반환할 결과 수
            threshold: 유사도 임계값
            
        Returns:
            (원본 텍스트, 유사도 점수, ID)의 튜플 리스트
        """
        session = self.get_session()
        
        try:
            # 벡터 유사도 검색: 코사인 유사도 사용
            from sqlalchemy import text
            
            # 벡터 간의 코사인 거리 계산 (1 - 코사인 유사도)
            # pgvector에서는 <=> 연산자가 코사인 거리를 계산함
            query = session.query(
                IdealAnswer.source,
                IdealAnswer.idea_id
            ).order_by(
                IdealAnswer.embedding.cosine_distance(query_embedding)
            ).filter(
                IdealAnswer.embedding.cosine_distance(query_embedding) <= (1 - threshold)
            ).limit(top_k)
            
            results = query.all()
            
            # 유사도 점수 계산 (0~1 사이, 높을수록 유사)
            similar_results = []
            for source, idea_id in results:
                # 다시 유사도 점수를 계산
                similarity_score_query = session.query(
                    1 - IdealAnswer.embedding.cosine_distance(query_embedding).label('similarity')
                ).filter(IdealAnswer.idea_id == idea_id).scalar()
                
                similar_results.append((source, similarity_score_query, idea_id))
            
            logger.info(f"유사도 검색 완료: {len(similar_results)}개 결과 반환")
            return similar_results
        except Exception as e:
            logger.error(f"유사도 검색 실패: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_embedding_by_id(self, idea_id: UUID) -> Optional[Tuple[str, List[float], UUID]]:
        """
        ID를 기반으로 임베딩 정보를 가져옵니다.
        
        Args:
            idea_id: 임베딩 ID
            
        Returns:
            (원본 텍스트, 임베딩 벡터, ID)의 튜플 또는 None
        """
        session = self.get_session()
        
        try:
            result = session.query(
                IdealAnswer.source,
                IdealAnswer.embedding,
                IdealAnswer.idea_id
            ).filter(IdealAnswer.idea_id == idea_id).first()
            
            if result:
                return (result[0], result[1], result[2])
            else:
                return None
        except Exception as e:
            logger.error(f"ID로 임베딩 검색 실패: {str(e)}")
            raise
        finally:
            session.close()
    
    def delete_embedding(self, idea_id: UUID) -> bool:
        """
        ID를 기반으로 임베딩을 삭제합니다.
        
        Args:
            idea_id: 삭제할 임베딩 ID
            
        Returns:
            삭제 성공 여부
        """
        session = self.get_session()
        
        try:
            result = session.query(IdealAnswer).filter(IdealAnswer.idea_id == idea_id).delete()
            session.commit()
            
            if result > 0:
                logger.info(f"임베딩 삭제 완료: {idea_id}")
                return True
            else:
                logger.warning(f"삭제할 임베딩을 찾을 수 없음: {idea_id}")
                return False
        except Exception as e:
            session.rollback()
            logger.error(f"임베딩 삭제 실패: {str(e)}")
            raise
        finally:
            session.close()
    
    def update_embedding(self, idea_id: UUID, new_source: str = None, 
                         new_embedding: List[float] = None) -> bool:
        """
        ID를 기반으로 임베딩을 업데이트합니다.
        
        Args:
            idea_id: 업데이트할 임베딩 ID
            new_source: 새로운 원본 텍스트 (선택사항)
            new_embedding: 새로운 임베딩 벡터 (선택사항)
            
        Returns:
            업데이트 성공 여부
        """
        session = self.get_session()
        
        try:
            ideal_answer = session.query(IdealAnswer).filter(IdealAnswer.idea_id == idea_id).first()
            
            if ideal_answer is None:
                logger.warning(f"업데이트할 임베딩을 찾을 수 없음: {idea_id}")
                return False
            
            if new_source is not None:
                ideal_answer.source = new_source
            if new_embedding is not None:
                ideal_answer.embedding = new_embedding
            
            session.commit()
            logger.info(f"임베딩 업데이트 완료: {idea_id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"임베딩 업데이트 실패: {str(e)}")
            raise
        finally:
            session.close()


class EmbeddingService:
    """
    임베딩 생성 및 관리를 위한 서비스 클래스
    """
    
    def __init__(self, vector_db_manager: VectorDBManager, model_name: str = "text-embedding-ada-002"):
        """
        EmbeddingService 초기화
        
        Args:
            vector_db_manager: 벡터 DB 매니저 인스턴스
            model_name: 임베딩 모델 이름
        """
        self.vector_db_manager = vector_db_manager
        self.model_name = model_name
        
        # OpenAI 클라이언트 초기화
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.openai_api_key)
        except ImportError:
            raise ImportError("OpenAI API 사용을 위해 'openai' 패키지를 설치해야 합니다: pip install openai")
        except Exception as e:
            logger.error(f"OpenAI 클라이언트 초기화 실패: {str(e)}")
            raise
    
    def create_embedding(self, text: str) -> List[float]:
        """
        텍스트에서 임베딩을 생성합니다.
        
        Args:
            text: 임베딩을 생성할 텍스트
            
        Returns:
            임베딩 벡터
        """
        try:
            # 텍스트가 너무 길 경우 자르기 (OpenAI는 최대 8192토큰)
            max_length = 8000  # 여유를 두고 8000자로 제한
            if len(text) > max_length:
                logger.warning(f"텍스트가 너무 깁니다. {max_length}자로 자릅니다: {text[:50]}...")
                text = text[:max_length]
            
            response = self.client.embeddings.create(
                input=text,
                model=self.model_name
            )
            
            embedding = response.data[0].embedding
            logger.info(f"임베딩 생성 완료: 길이 {len(embedding)}")
            return embedding
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {str(e)}")
            raise
    
    def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        여러 텍스트에서 임베딩을 일괄 생성합니다.
        
        Args:
            texts: 임베딩을 생성할 텍스트 목록
            
        Returns:
            임베딩 벡터 목록
        """
        try:
            # 각 텍스트가 너무 길 경우 자르기
            processed_texts = []
            for text in texts:
                max_length = 8000  # 여유를 두고 8000자로 제한
                if len(text) > max_length:
                    logger.warning(f"텍스트가 너무 깁니다. {max_length}자로 자릅니다.")
                    processed_texts.append(text[:max_length])
                else:
                    processed_texts.append(text)
            
            response = self.client.embeddings.create(
                input=processed_texts,
                model=self.model_name
            )
            
            embeddings = [data.embedding for data in response.data]
            logger.info(f"{len(embeddings)}개 임베딩 일괄 생성 완료")
            return embeddings
        except Exception as e:
            logger.error(f"임베딩 일괄 생성 실패: {str(e)}")
            raise
    
    def store_text_with_embedding(self, 
                                  text: str, 
                                  analysis_id: Optional[UUID] = None) -> UUID:
        """
        텍스트와 그 임베딩을 데이터베이스에 저장합니다.
        
        Args:
            text: 저장할 텍스트
            analysis_id: 분석 결과 ID (선택사항)
            
        Returns:
            저장된 레코드의 ID
        """
        # 임베딩 생성
        embedding = self.create_embedding(text)
        
        # 데이터베이스에 저장
        record_id = self.vector_db_manager.store_embedding(
            source=text,
            embedding=embedding,
            analysis_id=analysis_id
        )
        
        return record_id
    
    def store_texts_with_embeddings(self, 
                                    texts: List[str], 
                                    analysis_ids: Optional[List[UUID]] = None) -> List[UUID]:
        """
        여러 텍스트와 그 임베딩을 일괄 저장합니다.
        
        Args:
            texts: 저장할 텍스트 목록
            analysis_ids: 분석 결과 ID 목록 (선택사항)
            
        Returns:
            저장된 레코드의 ID 목록
        """
        # 임베딩 일괄 생성
        embeddings = self.create_embeddings_batch(texts)
        
        # 데이터베이스에 일괄 저장
        record_ids = self.vector_db_manager.store_embeddings_batch(
            sources=texts,
            embeddings=embeddings,
            analysis_ids=analysis_ids
        )
        
        return record_ids