"""
TOC(목차) 기반 RAG 시스템
rag_test의 새로운 방식을 통합한 고급 RAG 구현체
"""
import json
import uuid
import psycopg2
import psycopg2.extras as extras
from typing import List, Dict, Any, Tuple, Optional
from uuid import UUID
from pathlib import Path
from openai import OpenAI

from .rag_interface import AdvancedRAGInterface, RAGConfig
from app.core.config import settings


class TOCBasedRAG(AdvancedRAGInterface):
    """목차 기반 고급 RAG 시스템"""
    
    def __init__(self, config: RAGConfig):
        super().__init__(config)
        self.openai_client = OpenAI(api_key=settings.openai_api_key)
        self.db_connection = self._get_db_connection()
        
    def _get_db_connection(self):
        """데이터베이스 연결 생성"""
        return psycopg2.connect(settings.database_url)
    
    def load_and_process_file(self, 
                             source_path: str, 
                             **kwargs) -> List[Dict[str, Any]]:
        """파일을 로드하고 TOC 기반으로 처리"""
        # TODO: rag_test의 bucket.py + toc_extract.py + chunking.py 로직 통합
        raise NotImplementedError("TOC 기반 파일 처리 구현 필요")
    
    def search_similar(self, 
                      query: str, 
                      top_k: int = 5, 
                      threshold: float = 0.5) -> List[Tuple[str, float, UUID]]:
        """벡터 유사도 검색"""
        # 쿼리 임베딩 생성
        query_embedding = self._create_embedding(query)
        
        # pgvector KNN 검색
        sql = """
        SELECT section_id, canonical_path, full_text, 
               embedding <=> %s::vector as distance
        FROM ref_handbook_snippet 
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
        
        sql = """
        INSERT INTO ref_handbook_snippet 
        (section_id, canonical_path, full_text, embedding)
        VALUES (%s, %s, %s, %s)
        """
        
        with self.db_connection.cursor() as cur:
            cur.execute(sql, (doc_id, kwargs.get('path', ''), text, embedding))
            self.db_connection.commit()
        
        return UUID(doc_id)
    
    def batch_add_documents(self, texts: List[str], **kwargs) -> List[UUID]:
        """여러 문서 일괄 추가"""
        doc_ids = []
        for text in texts:
            doc_id = self.add_document(text, **kwargs)
            doc_ids.append(doc_id)
        return doc_ids
    
    def search_by_analysis_result(self, 
                                 analysis_id: str, 
                                 **kwargs) -> List[Dict[str, Any]]:
        """분석 결과 기반 검색 (summary_rag.py 로직)"""
        # 분석 결과 조회
        analysis = self._fetch_analysis_by_id(analysis_id)
        if not analysis:
            return []
        
        # 요약 텍스트로 임베딩 생성
        summary = analysis.get('summary', '')
        if not summary:
            return []
        
        # 벡터 검색
        results = self.search_similar(summary, **kwargs)
        
        # 섹션별로 그룹화하고 스티칭
        section_ids = list(set([result[2] for result in results]))
        full_sections = self._fetch_full_sections(section_ids)
        
        return full_sections
    
    def generate_advice(self, 
                       analysis_id: str, 
                       **kwargs) -> Dict[str, Any]:
        """조언 생성 (advice.py 로직)"""
        # 관련 섹션 검색
        sections = self.search_by_analysis_result(analysis_id, **kwargs)
        
        if not sections:
            return {"advice": "관련 정보를 찾을 수 없습니다.", "sources": []}
        
        # 분석 결과 조회
        analysis = self._fetch_analysis_by_id(analysis_id)
        
        # 프롬프트 구성
        context = "\n\n".join([
            f"[{sec['canonical_path']}]\n{sec['full_text']}" 
            for sec in sections
        ])
        
        prompt = f"""
다음은 가족 대화 분석 결과입니다:
{analysis.get('summary', '')}

관련 전문가 조언:
{context}

위 정보를 바탕으로 구체적이고 실용적인 조언을 제공해주세요.
"""
        
        # OpenAI API 호출
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        advice = response.choices[0].message.content
        sources = [{"path": sec['canonical_path'], "citation": sec.get('citations', [])} 
                  for sec in sections]
        
        return {
            "advice": advice,
            "sources": sources,
            "analysis_id": analysis_id
        }
    
    def save_feedback(self, 
                     analysis_id: str, 
                     feedback: str, 
                     **kwargs) -> bool:
        """피드백 저장 (advice_save.py 로직)"""
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
            model=self.config.extra_config.get('embedding_model', 'text-embedding-3-small'),
            input=text
        )
        return response.data[0].embedding
    
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
        
        sql = """
        SELECT section_id, canonical_path, chunk_ix,
               page_start, page_end, citation, full_text
        FROM ref_handbook_snippet
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
