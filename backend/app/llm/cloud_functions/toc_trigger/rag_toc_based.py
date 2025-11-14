"""
TOC(목차) 기반 RAG 시스템
SQLAlchemy + pgvector를 사용한 벡터 DB 연동
"""
import json
import tempfile
import logging
from typing import List, Dict, Any, Tuple, Optional
from uuid import UUID, uuid4, uuid5, NAMESPACE_DNS
from pathlib import Path
from openai import OpenAI

from sqlalchemy import create_engine, Column, String, Text, Integer
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# pgvector import 시도
try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
    print("✅ pgvector 임포트 성공")
except ImportError as e:
    print(f"❌ pgvector 임포트 실패: {e}")
    PGVECTOR_AVAILABLE = False
    # 대체 타입 정의
    from sqlalchemy import ARRAY, Float
    Vector = lambda dim: ARRAY(Float, dimensions=dim)

from rag_interface import AdvancedRAGInterface, RAGConfig
from toc_utils import TOCExtractor
from toc_chunker import TOCChunker
from gcp_utils import GCPStorageManager
from config import settings

# 베이스 클래스
Base = declarative_base()

class IdealAnswer(Base):
    """이상적인 답변 테이블 모델"""
    __tablename__ = 'ideal_answer'
    
    snippet_id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    book_id = Column(PostgreSQLUUID(as_uuid=True), nullable=True)
    book_title = Column(Text, nullable=True)
    l1_title = Column(Text, nullable=True)
    l2_title = Column(Text, nullable=True)
    l3_title = Column(Text, nullable=True)
    canonical_path = Column(Text, nullable=True)
    section_id = Column(Text, nullable=True)
    chunk_ix = Column(Integer, nullable=True)
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    citation = Column(Text, nullable=True)
    full_text = Column(Text, nullable=True)
    embed_text = Column(Text, nullable=True)
    embedding = Column(Vector(1536), nullable=True)
    rag_type = Column(String(20), nullable=True, default='toc')


class TOCBasedRAG(AdvancedRAGInterface):
    """목차 기반 고급 RAG 시스템"""
    
    def __init__(self, config: RAGConfig):
        super().__init__(config)
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        
        # SQLAlchemy 엔진 및 세션 설정
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # 유틸리티 초기화
        self.toc_extractor = TOCExtractor()
        self.toc_chunker = TOCChunker()
        self.gcp_manager = GCPStorageManager(config.extra_config.get("bucket_name"))
        
        # 설정
        self.table_name = config.extra_config.get("table_name", "ideal_answer")
        self.embedding_model = config.extra_config.get("embedding_model", "text-embedding-3-small")
        
    def _create_engine(self):
        """SQLAlchemy 엔진 생성"""
        db_url = settings.database_url
        print("데이터베이스 연결 시도...")
        
        # PostgreSQL + pgvector용 URL 형식 확인
        if not db_url.startswith("postgresql"):
            raise ValueError("PostgreSQL URL이 필요합니다")
        
        # SQLAlchemy 형식으로 변환 (필요시)
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://")
        
        try:
            engine = create_engine(
                db_url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=300
            )
            print("SQLAlchemy 엔진 생성 성공")
            return engine
        except Exception as e:
            print(f"SQLAlchemy 엔진 생성 실패: {e}")
            raise
    
    def load_and_process_file(self, 
                             source_path: str, 
                             **kwargs) -> List[Dict[str, Any]]:
        """파일을 로드하고 TOC 기반으로 처리"""
        results = []
        
        try:
            # 원본 파일명 추출
            original_filename = Path(source_path).name if source_path.startswith("gs://") else Path(source_path).stem
            
            # GCP에서 파일 다운로드 (필요한 경우)
            if source_path.startswith("gs://") or not Path(source_path).exists():
                local_path = self.gcp_manager.download_single_file(source_path)
            else:
                local_path = source_path
            
            # 1. TOC 추출 (원본 파일명 전달)
            try:
                toc_data = self.toc_extractor.extract_toc_from_pdf(local_path)
                # 원본 파일명을 TOC 데이터에 추가
                for entry in toc_data:
                    entry["book_name"] = Path(original_filename).stem
                    
                print(f"TOC 추출 결과: {len(toc_data)}개 항목")
                if toc_data:
                    print(f"첫 번째 TOC 항목: {toc_data[0]}")
                else:
                    print("TOC 데이터가 비어있음")
                    return [{"status": "error", "message": "TOC를 추출할 수 없습니다."}]
            except Exception as e:
                print(f"TOC 추출 중 오류: {str(e)}")
                return [{"status": "error", "message": f"TOC 추출 오류: {str(e)}"}]
            
            # 2. TOC 기반 청킹
            chunks = self.toc_chunker.chunk_pdf_by_toc(local_path, toc_data)
            print(f"청킹 결과: {len(chunks)}개 청크")
            
            # 3. 각 청크에 대해 임베딩 생성 및 저장
            for i, chunk in enumerate(chunks):
                try:
                    # 임베딩 생성
                    embedding = self._create_embedding(chunk["embed_text"])
                    
                    # 데이터베이스에 저장
                    chunk_id = self._save_chunk_to_db(chunk, embedding)
                    
                    results.append({
                        "chunk_id": chunk_id,
                        "section_id": chunk["section_id"],
                        "canonical_path": chunk["canonical_path"],
                        "status": "success"
                    })
                    
                    if i % 10 == 0:
                        print(f"처리 진행률: {i+1}/{len(chunks)}")
                    
                except Exception as e:
                    print(f"청크 {i} 처리 실패: {e}")
                    results.append({
                        "chunk_id": chunk.get("chunk_id"),
                        "status": "error",
                        "error": str(e)
                    })
            
            # 임시 파일 정리
            if local_path != source_path:
                Path(local_path).unlink(missing_ok=True)
            
            return results
            
        except Exception as e:
            print(f"파일 처리 실패: {str(e)}")
            return [{"status": "error", "message": f"파일 처리 실패: {str(e)}"}]
    
    def _save_chunk_to_db(self, chunk: Dict[str, Any], embedding: List[float]) -> str:
        """청크를 데이터베이스에 저장 (SQLAlchemy 방식)"""
        session = self.SessionLocal()
        try:
            # book_id 생성 (파일명 기반으로 일관된 UUID)
            book_title = chunk.get("book_title", "Unknown")
            book_id = uuid5(NAMESPACE_DNS, book_title)
            
            # 중복 체크: 같은 book_id + canonical_path + chunk_ix 조합 확인
            existing = session.query(IdealAnswer).filter(
                IdealAnswer.book_id == book_id,
                IdealAnswer.canonical_path == chunk.get("canonical_path"),
                IdealAnswer.chunk_ix == chunk.get("chunk_ix")
            ).first()
            
            if existing:
                print(f"중복 데이터 스킵: {chunk.get('canonical_path')} (chunk {chunk.get('chunk_ix')})")
                return str(existing.snippet_id)
            
            # IdealAnswer 객체 생성
            ideal_answer = IdealAnswer(
                book_id=book_id,
                book_title=chunk.get("book_title"),
                l1_title=chunk.get("l1_title"),
                l2_title=chunk.get("l2_title"), 
                l3_title=chunk.get("l3_title"),
                canonical_path=chunk.get("canonical_path"),
                section_id=chunk.get("section_id"),
                chunk_ix=chunk.get("chunk_ix"),
                page_start=chunk.get("page_start"),
                page_end=chunk.get("page_end"),
                citation=chunk.get("citation"),
                full_text=chunk.get("full_text"),
                embed_text=chunk.get("embed_text"),
                embedding=embedding,
                rag_type='toc'
            )
            
            session.add(ideal_answer)
            session.commit()
            
            chunk_id = str(ideal_answer.snippet_id)
            return chunk_id
            
        except Exception as e:
            session.rollback()
            print(f"청크 저장 실패: {e}")
            raise
        finally:
            session.close()
    
    def search_similar(self, 
                      query: str, 
                      top_k: int = 5,
                      **kwargs) -> List[Tuple[str, float, str]]:
        """유사한 텍스트 검색 (SQLAlchemy + pgvector)"""
        session = self.SessionLocal()
        try:
            # 쿼리 임베딩 생성
            query_embedding = self._create_embedding(query)
            
            if PGVECTOR_AVAILABLE:
                # pgvector를 사용한 유사도 검색
                results = session.query(
                    IdealAnswer.embed_text,
                    IdealAnswer.embedding.cosine_distance(query_embedding).label('distance'),
                    IdealAnswer.snippet_id
                ).filter(
                    IdealAnswer.rag_type == 'toc'
                ).order_by(
                    IdealAnswer.embedding.cosine_distance(query_embedding)
                ).limit(top_k).all()
                
                # 거리를 유사도로 변환 (1 - distance)
                return [(text, 1 - distance, str(snippet_id)) for text, distance, snippet_id in results]
            else:
                # pgvector 없이 기본 검색 (임시)
                print("⚠️ pgvector 없이 기본 검색 수행")
                results = session.query(
                    IdealAnswer.embed_text,
                    IdealAnswer.snippet_id
                ).filter(
                    IdealAnswer.rag_type == 'toc'
                ).limit(top_k).all()
                
                return [(text, 0.5, str(snippet_id)) for text, snippet_id in results]
            
        except Exception as e:
            print(f"검색 실패: {e}")
            raise
        finally:
            session.close()
    
    def _create_embedding(self, text: str) -> List[float]:
        """OpenAI 임베딩 생성"""
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"임베딩 생성 실패: {e}")
            raise
    
    def add_document(self, text: str, **kwargs) -> UUID:
        """단일 문서 추가"""
        embedding = self._create_embedding(text)
        
        chunk_data = {
            "section_id": kwargs.get('section_id', str(uuid4())),
            "canonical_path": kwargs.get('path', ''),
            "full_text": text,
            "embed_text": text,
            "citation": kwargs.get('citation', ''),
            "chunk_ix": 0,
            "page_start": kwargs.get('page', 1),
            "page_end": kwargs.get('page', 1)
        }
        
        chunk_id = self._save_chunk_to_db(chunk_data, embedding)
        return UUID(chunk_id)
    
    def batch_add_documents(self, texts: List[str], **kwargs) -> List[UUID]:
        """여러 문서 일괄 추가"""
        doc_ids = []
        for i, text in enumerate(texts):
            doc_kwargs = {k: v[i] if isinstance(v, list) else v for k, v in kwargs.items()}
            doc_id = self.add_document(text, **doc_kwargs)
            doc_ids.append(doc_id)
        return doc_ids
    
    def search_by_analysis_result(self, analysis_id: str, **kwargs) -> List[Dict[str, Any]]:
        """분석 결과 기반 검색 (구현 필요시 추가)"""
        return []
    
    def generate_advice(self, analysis_id: str, **kwargs) -> Dict[str, Any]:
        """조언 생성 (구현 필요시 추가)"""
        return {"advice": "TOC 기반 조언 생성 기능은 구현 예정입니다.", "sources": []}
    
    def save_feedback(self, analysis_id: str, feedback: str, **kwargs) -> bool:
        """피드백 저장 (구현 필요시 추가)"""
        return True
