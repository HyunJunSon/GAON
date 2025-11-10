"""
RAG(Retrieval Augmented Generation) 시스템의 메인 통합 모듈
"""
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

from app.llm.rag.loaders.document_loader import DocumentLoader, Document
from app.llm.rag.extractors.document_extractors import ExtractorFactory
from app.llm.rag.storage.storage_adapter import StorageAdapterFactory
from app.llm.rag.chunkers.chunking_strategies import ChunkerFactory
from app.llm.rag.vector_db.vector_db_manager import VectorDBManager, EmbeddingService
from app.llm.rag.logger import rag_logger
from app.llm.rag.exception import DocumentLoadException, ExtractionException, \
    ChunkingException, StorageException, VectorDBException, EmbeddingException

logger = rag_logger


class RAGSystem:
    """
    RAG 시스템의 메인 클래스
    문서 로딩, 추출, 청킹, 임베딩, 저장, 검색 기능을 통합
    """
    
    def __init__(self, 
                 storage_type: str = "local",
                 chunker_type: str = "recursive",
                 **storage_kwargs):
        """
        RAG 시스템 초기화
        
        Args:
            storage_type: 스토리지 유형 ('local', 'gcp', 's3' 등)
            chunker_type: 청킹 전략 유형
            **storage_kwargs: 스토리지 어댑터에 전달할 추가 인자
        """
        try:
            # 구성 요소 초기화
            self.storage_adapter = StorageAdapterFactory().get_adapter(
                storage_type=storage_type,
                **storage_kwargs
            )
            self.document_loader = DocumentLoader()
            self.extractor_factory = ExtractorFactory()
            self.chunker_factory = ChunkerFactory()
            self.vector_db_manager = VectorDBManager()
            self.embedding_service = EmbeddingService(self.vector_db_manager)
            
            # 설정 저장
            self.storage_type = storage_type
            self.chunker_type = chunker_type
            
            logger.info(f"RAG 시스템 초기화 완료 (스토리지: {storage_type}, 청킹: {chunker_type})")
        except Exception as e:
            logger.error(f"RAG 시스템 초기화 실패: {str(e)}")
            raise
    
    def load_and_process_file(self, 
                             source_path: str, 
                             chunk_kwargs: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        파일을 로드하고 처리하여 임베딩을 생성합니다.
        
        Args:
            source_path: 소스 파일 경로
            chunk_kwargs: 청킹 전략에 전달할 추가 인자 (선택사항)
            
        Returns:
            처리 결과 정보
        """
        if chunk_kwargs is None:
            chunk_kwargs = {}
        
        logger.info(f"파일 처리 시작: {source_path}")
        
        try:
            # 1. 문서 로드
            documents = self.document_loader.load_documents(source_path)
            logger.info(f"{len(documents)}개의 문서 로드 완료")
            
            # 2. 각 문서 청킹 및 임베딩 생성
            results = []
            for doc in documents:
                chunks = self.chunker_factory.chunk_by_format(
                    text=doc.content,
                    file_format=Path(source_path).suffix.lower(),
                    metadata=doc.metadata,
                    source=source_path,
                    **chunk_kwargs
                )
                
                logger.info(f"{len(chunks)}개의 청크 생성 완료")
                
                # 3. 각 청크에 대해 임베딩 생성 및 저장
                for chunk in chunks:
                    # 임베딩 생성
                    embedding = self.embedding_service.create_embedding(chunk.content)
                    
                    # 벡터 데이터베이스에 저장
                    record_id = self.vector_db_manager.store_embedding(
                        source=chunk.content,
                        embedding=embedding,
                        analysis_id=None  # 필요 시 analysis_id 전달
                    )
                    
                    results.append({
                        'chunk': chunk,
                        'embedding_id': record_id,
                        'status': 'success'
                    })
                    
                    logger.info(f"청크 임베딩 저장 완료: {record_id}")
            
            logger.info(f"파일 처리 완료: {source_path}, 총 {len(results)}개 청크 처리됨")
            return results
            
        except Exception as e:
            logger.error(f"파일 처리 실패 {source_path}: {str(e)}")
            raise DocumentLoadException(f"파일 처리 실패 {source_path}: {str(e)}", original_exception=e)
    
    def load_and_process_from_storage(self, 
                                     storage_path: str, 
                                     local_destination: str = None,
                                     chunk_kwargs: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        스토리지에서 파일을 다운로드하고 처리합니다.
        
        Args:
            storage_path: 스토리지 경로
            local_destination: 로컬 다운로드 경로 (선택사항, 기본값은 임시 디렉토리)
            chunk_kwargs: 청킹 전략에 전달할 추가 인자 (선택사항)
            
        Returns:
            처리 결과 정보
        """
        if chunk_kwargs is None:
            chunk_kwargs = {}
        
        # 임시 디렉토리 설정
        if local_destination is None:
            import tempfile
            local_destination = tempfile.mktemp(
                prefix="rag_",
                suffix=Path(storage_path).suffix
            )
        
        logger.info(f"스토리지 파일 처리 시작: {storage_path}")
        
        try:
            # 1. 스토리지에서 파일 다운로드
            downloaded_path = self.storage_adapter.download_file(
                source_identifier=storage_path,
                destination_path=local_destination
            )
            
            logger.info(f"파일 다운로드 완료: {downloaded_path}")
            
            # 2. 다운로드한 파일 처리
            results = self.load_and_process_file(
                source_path=downloaded_path,
                chunk_kwargs=chunk_kwargs
            )
            
            # 3. 로컬 임시 파일 삭제 (임시 파일인 경우)
            if local_destination.startswith(tempfile.gettempdir()) or \
               local_destination != local_destination:  # 실제로 임시 파일인지 확인
                import os
                os.remove(local_destination)
                logger.info(f"임시 파일 삭제: {local_destination}")
            
            logger.info(f"스토리지 파일 처리 완료: {storage_path}")
            return results
            
        except Exception as e:
            logger.error(f"스토리지 파일 처리 실패 {storage_path}: {str(e)}")
            raise StorageException(f"스토리지 파일 처리 실패 {storage_path}: {str(e)}", original_exception=e)
    
    def process_multiple_files(self, 
                              file_paths: List[str], 
                              chunk_kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        여러 파일을 처리합니다.
        
        Args:
            file_paths: 파일 경로 목록
            chunk_kwargs: 청킹 전략에 전달할 추가 인자 (선택사항)
            
        Returns:
            파일 경로별 처리 결과 정보
        """
        if chunk_kwargs is None:
            chunk_kwargs = {}
        
        results = {}
        
        for file_path in file_paths:
            try:
                logger.info(f"다중 파일 처리 - 현재 파일: {file_path}")
                results[file_path] = self.load_and_process_file(
                    source_path=file_path,
                    chunk_kwargs=chunk_kwargs
                )
            except Exception as e:
                logger.error(f"다중 파일 처리 실패 {file_path}: {str(e)}")
                results[file_path] = [{
                    'status': 'error',
                    'error': str(e),
                    'error_type': type(e).__name__
                }]
        
        logger.info(f"다중 파일 처리 완료: {len(file_paths)}개 파일 처리됨")
        return results
    
    def search_similar(self, 
                      query: str, 
                      top_k: int = 5, 
                      threshold: float = 0.5) -> List[Tuple[str, float, UUID]]:
        """
        유사한 문서를 검색합니다.
        
        Args:
            query: 쿼리 텍스트
            top_k: 반환할 결과 수
            threshold: 유사도 임계값
            
        Returns:
            (원본 텍스트, 유사도 점수, ID)의 튜플 리스트
        """
        logger.info(f"유사도 검색 시작: '{query[:50]}...'")
        
        try:
            # 1. 쿼리 임베딩 생성
            query_embedding = self.embedding_service.create_embedding(query)
            
            # 2. 유사한 임베딩 검색
            results = self.vector_db_manager.find_similar(
                query_embedding=query_embedding,
                top_k=top_k,
                threshold=threshold
            )
            
            logger.info(f"유사도 검색 완료: {len(results)}개 결과 반환")
            return results
        except Exception as e:
            logger.error(f"유사도 검색 실패: {str(e)}")
            raise VectorDBException(f"유사도 검색 실패: {str(e)}", original_exception=e)
    
    def add_document(self, 
                    text: str, 
                    analysis_id: Optional[UUID] = None) -> UUID:
        """
        단일 문서 텍스트를 임베딩하여 저장합니다.
        
        Args:
            text: 저장할 텍스트
            analysis_id: 분석 결과 ID (선택사항)
            
        Returns:
            저장된 레코드의 ID
        """
        logger.info(f"단일 문서 추가 시작: {text[:50]}...")
        
        try:
            # 1. 임베딩 생성 및 저장
            record_id = self.embedding_service.store_text_with_embedding(
                text=text,
                analysis_id=analysis_id
            )
            
            logger.info(f"단일 문서 추가 완료: {record_id}")
            return record_id
        except Exception as e:
            logger.error(f"단일 문서 추가 실패: {str(e)}")
            raise EmbeddingException(f"문서 추가 실패: {str(e)}", original_exception=e)
    
    def batch_add_documents(self, 
                           texts: List[str], 
                           analysis_ids: Optional[List[UUID]] = None) -> List[UUID]:
        """
        여러 문서 텍스트를 일괄 임베딩하여 저장합니다.
        
        Args:
            texts: 저장할 텍스트 목록
            analysis_ids: 분석 결과 ID 목록 (선택사항)
            
        Returns:
            저장된 레코드의 ID 목록
        """
        logger.info(f"문서 일괄 추가 시작: {len(texts)}개 문서")
        
        try:
            # 1. 임베딩 일괄 생성 및 저장
            record_ids = self.embedding_service.store_texts_with_embeddings(
                texts=texts,
                analysis_ids=analysis_ids
            )
            
            logger.info(f"문서 일괄 추가 완료: {len(record_ids)}개 저장됨")
            return record_ids
        except Exception as e:
            logger.error(f"문서 일괄 추가 실패: {str(e)}")
            raise EmbeddingException(f"문서 일괄 추가 실패: {str(e)}", original_exception=e)


# 예시 사용법
def main():
    """
    RAG 시스템 사용 예시
    """
    # 1. RAG 시스템 초기화 (로컬 스토리지 사용)
    rag_system = RAGSystem(storage_type="gcp", bucket_name="gaon-cloud-data")
    
    # 2. 단일 파일 처리
    # result = rag_system.load_and_process_file("path/to/your/document.pdf")
    
    # 3. 쿼리 기반 유사 문서 검색
    # search_results = rag_system.search_similar("검색하고 싶은 질의")
    
    # 4. 텍스트 직접 추가
    # new_id = rag_system.add_document("추가하고 싶은 텍스트 내용")
    
    print("RAG 시스템 초기화 완료 예시")


if __name__ == "__main__":
    main()