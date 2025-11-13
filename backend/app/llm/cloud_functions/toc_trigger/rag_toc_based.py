"""
TOC(목차) 기반 RAG 시스템
rag_test의 새로운 방식을 통합한 고급 RAG 구현체
"""
import json
import uuid
import tempfile
import psycopg2
import psycopg2.extras as extras
from typing import List, Dict, Any, Tuple, Optional
from uuid import UUID
from pathlib import Path
from openai import OpenAI

from rag_interface import AdvancedRAGInterface, RAGConfig
from toc_utils import TOCExtractor
from toc_chunker import TOCChunker
from gcp_utils import GCPStorageManager
from core.config import settings


class TOCBasedRAG(AdvancedRAGInterface):
    """목차 기반 고급 RAG 시스템"""
    
    def __init__(self, config: RAGConfig):
        super().__init__(config)
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.db_connection = self._get_db_connection()
        
        # 유틸리티 초기화
        self.toc_extractor = TOCExtractor()
        self.toc_chunker = TOCChunker()
        self.gcp_manager = GCPStorageManager(config.extra_config.get("bucket_name"))
        
        # 설정
        self.table_name = config.extra_config.get("table_name", "ref_handbook_snippet")
        self.embedding_model = config.extra_config.get("embedding_model", "text-embedding-3-small")
        
    def _get_db_connection(self):
        """데이터베이스 연결 생성"""
        # SQLAlchemy 형식을 psycopg2 형식으로 변환
        db_url = settings.database_url
        if db_url.startswith("postgresql+psycopg2://"):
            db_url = db_url.replace("postgresql+psycopg2://", "postgresql://")
        return psycopg2.connect(db_url)
    
    def load_and_process_file(self, 
                             source_path: str, 
                             **kwargs) -> List[Dict[str, Any]]:
        """파일을 로드하고 TOC 기반으로 처리"""
        results = []
        
        try:
            # GCP에서 파일 다운로드 (필요한 경우)
            if source_path.startswith("gs://") or not Path(source_path).exists():
                local_path = self.gcp_manager.download_single_file(source_path)
            else:
                local_path = source_path
            
            # 1. TOC 추출
            try:
                toc_data = self.toc_extractor.extract_toc_from_pdf(local_path)
                logging.info(f"TOC 추출 결과: {len(toc_data)}개 항목")
                if toc_data:
                    logging.info(f"첫 번째 TOC 항목: {toc_data[0]}")
                else:
                    logging.warning("TOC 데이터가 비어있음")
                    return [{"status": "error", "message": "TOC를 추출할 수 없습니다."}]
            except Exception as e:
                logging.error(f"TOC 추출 중 오류: {str(e)}")
                return [{"status": "error", "message": f"TOC 추출 오류: {str(e)}"}]
            
            # 2. TOC 기반 청킹
            chunks = self.toc_chunker.chunk_pdf_by_toc(local_path, toc_data)
            
            # 3. 각 청크에 대해 임베딩 생성 및 저장
            for chunk in chunks:
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
                    
                except Exception as e:
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
            return [{"status": "error", "message": f"파일 처리 실패: {str(e)}"}]
    
    def search_similar(self, 
                      query: str, 
                      top_k: int = 5, 
                      threshold: float = 0.5) -> List[Tuple[str, float, UUID]]:
        """벡터 유사도 검색"""
        query_embedding = self._create_embedding(query)
        
        sql = f"""
        SELECT section_id, canonical_path, full_text, 
               embedding <=> %s::vector as distance
        FROM {self.table_name}
        WHERE embedding <=> %s::vector < %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """
        
        with self.db_connection.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(sql, (query_embedding, query_embedding, 1-threshold, query_embedding, top_k))
            results = cur.fetchall()
        
        return [(row['full_text'], 1-row['distance'], row['section_id']) for row in results]
    
    def add_document(self, text: str, **kwargs) -> UUID:
        """단일 문서 추가"""
        embedding = self._create_embedding(text)
        doc_id = str(uuid.uuid4())
        
        chunk_data = {
            "chunk_id": doc_id,
            "section_id": doc_id,
            "canonical_path": kwargs.get('path', ''),
            "full_text": text,
            "embed_text": text,
            "citation": kwargs.get('citation', ''),
            "chunk_ix": 0,
            "page_start": kwargs.get('page', 1),
            "page_end": kwargs.get('page', 1)
        }
        
        self._save_chunk_to_db(chunk_data, embedding)
        return UUID(doc_id)
    
    def batch_add_documents(self, texts: List[str], **kwargs) -> List[UUID]:
        """여러 문서 일괄 추가"""
        doc_ids = []
        for i, text in enumerate(texts):
            doc_kwargs = {k: v[i] if isinstance(v, list) else v for k, v in kwargs.items()}
            doc_id = self.add_document(text, **doc_kwargs)
            doc_ids.append(doc_id)
        return doc_ids
    
    def search_by_analysis_result(self, 
                                 analysis_id: str, 
                                 **kwargs) -> List[Dict[str, Any]]:
        """분석 결과 기반 검색"""
        analysis = self._fetch_analysis_by_id(analysis_id)
        if not analysis:
            return []
        
        summary = analysis.get('summary', '')
        if not summary:
            return []
        
        # 벡터 검색
        top_k = kwargs.get('top_k', 10)
        threshold = kwargs.get('threshold', 0.5)
        results = self.search_similar(summary, top_k, threshold)
        
        # 섹션별로 그룹화하고 스티칭
        section_ids = list(set([result[2] for result in results]))
        full_sections = self._fetch_full_sections(section_ids)
        
        return full_sections
    
    def generate_advice(self, 
                       analysis_id: str, 
                       **kwargs) -> Dict[str, Any]:
        """조언 생성"""
        sections = self.search_by_analysis_result(analysis_id, **kwargs)
        
        if not sections:
            return {"advice": "관련 정보를 찾을 수 없습니다.", "sources": []}
        
        analysis = self._fetch_analysis_by_id(analysis_id)
        
        # 컨텍스트 구성
        context = "\n\n".join([
            f"[{sec['canonical_path']}]\n{sec['full_text']}" 
            for sec in sections[:3]  # 상위 3개 섹션만 사용
        ])
        
        prompt = f"""
다음은 가족 대화 분석 결과입니다:
{analysis.get('summary', '')}

관련 전문가 조언:
{context}

위 정보를 바탕으로 구체적이고 실용적인 조언을 제공해주세요.
조언은 한국어로 작성하고, 실제 적용 가능한 방법을 포함해주세요.
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            advice = response.choices[0].message.content
            sources = [{"path": sec['canonical_path'], "citations": sec.get('citations', [])} 
                      for sec in sections]
            
            return {
                "advice": advice,
                "sources": sources,
                "analysis_id": analysis_id
            }
            
        except Exception as e:
            return {
                "advice": f"조언 생성 중 오류가 발생했습니다: {str(e)}",
                "sources": [],
                "analysis_id": analysis_id
            }
    
    def save_feedback(self, 
                     analysis_id: str, 
                     feedback: str, 
                     **kwargs) -> bool:
        """피드백 저장"""
        try:
            sql = """
            UPDATE analysis_result 
            SET feedback = %s, updated_at = NOW()
            WHERE analysis_id = %s
            """
            
            with self.db_connection.cursor() as cur:
                cur.execute(sql, (feedback, analysis_id))
                self.db_connection.commit()
            
            return cur.rowcount > 0
        except Exception:
            return False
    
    def _create_embedding(self, text: str) -> List[float]:
        """OpenAI 임베딩 생성"""
        response = self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding
    
    def _save_chunk_to_db(self, chunk_data: Dict[str, Any], embedding: List[float]) -> str:
        """청크 데이터를 데이터베이스에 저장"""
        from app.llm.rag.vector_db.vector_db_manager import VectorDBManager
        
        # VectorDBManager 사용하여 저장
        vector_manager = VectorDBManager()
        
        # 메타데이터 구성
        metadata = {
            'l1_title': chunk_data.get('l1_title'),
            'l2_title': chunk_data.get('l2_title'), 
            'l3_title': chunk_data.get('l3_title'),
            'canonical_path': chunk_data.get('canonical_path'),
            'section_id': chunk_data.get('section_id'),
            'chunk_ix': chunk_data.get('chunk_ix'),
            'page_start': chunk_data.get('page_start'),
            'page_end': chunk_data.get('page_end'),
            'citation': chunk_data.get('citation'),
            'rag_type': 'toc_based'  # TOC 기반 RAG 타입 설정
        }
        
        # 저장
        snippet_id = vector_manager.store_embedding(
            embed_text=chunk_data.get('embed_text', ''),
            embedding=embedding,
            full_text=chunk_data.get('full_text', ''),
            **metadata
        )
        
        return str(snippet_id)
    
    def _fetch_analysis_by_id(self, analysis_id: str) -> Dict[str, Any]:
        """분석 결과 조회"""
        sql = "SELECT * FROM analysis_result WHERE analysis_id = %s LIMIT 1"
        with self.db_connection.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(sql, (analysis_id,))
            row = cur.fetchone()
        
        if not row:
            return {}
        
        # JSON 필드 파싱
        for k in ("statistics", "style_analysis"):
            if isinstance(row.get(k), str):
                try:
                    row[k] = json.loads(row[k])
                except:
                    pass
        
        return dict(row)
    
    def _fetch_full_sections(self, section_ids: List[str]) -> List[Dict[str, Any]]:
        """섹션별 전체 텍스트 조회 및 스티칭"""
        if not section_ids:
            return []
        
        sql = f"""
        SELECT section_id, canonical_path, chunk_ix,
               page_start, page_end, citation, full_text
        FROM {self.table_name}
        WHERE section_id = ANY(%s)
        ORDER BY section_id, chunk_ix, page_start, page_end
        """
        
        with self.db_connection.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(sql, (section_ids,))
            rows = cur.fetchall()
        
        # 섹션별로 그룹화
        sections_by_id = {}
        for row in rows:
            section_id = row['section_id']
            if section_id not in sections_by_id:
                sections_by_id[section_id] = {
                    'section_id': section_id,
                    'canonical_path': row['canonical_path'],
                    'snippets': [],
                    'citations': set()
                }
            
            sections_by_id[section_id]['snippets'].append(row)
            if row.get('citation'):
                sections_by_id[section_id]['citations'].add(row['citation'])
        
        # 섹션별 텍스트 스티칭
        sections = []
        for section_data in sections_by_id.values():
            full_text = "\n\n".join([
                snippet['full_text'] 
                for snippet in section_data['snippets'] 
                if snippet.get('full_text')
            ])
            
            sections.append({
                'section_id': section_data['section_id'],
                'canonical_path': section_data['canonical_path'],
                'full_text': full_text,
                'citations': list(section_data['citations'])
            })
        
        return sections
