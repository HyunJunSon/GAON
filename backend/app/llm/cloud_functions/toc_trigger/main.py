import functions_framework
import os
import sys
import tempfile
import logging

@functions_framework.cloud_event
def toc_pdf_processor(cloud_event):
    """TOC 기반 RAG 시스템으로 PDF 파일 처리"""
    
    try:
        # Pub/Sub 메시지에서 정보 추출
        message = cloud_event.data.get('message', {})
        attributes = message.get('attributes', {})
        
        bucket = attributes.get('bucketId')
        file_name = attributes.get('objectId')
        event_type = attributes.get('eventType')
        
        print(f"TOC RAG 처리 시작: {file_name}")
        
        # rag-data/toc-pdfs 경로만 처리
        if not file_name or not file_name.startswith('rag-data/toc-pdfs/'):
            print(f"TOC RAG 처리 제외: {file_name}")
            return
        
        # 파일 생성 이벤트만 처리
        if event_type != 'OBJECT_FINALIZE':
            print(f"처리하지 않는 이벤트: {event_type}")
            return
        
        # PDF 파일만 처리
        if not file_name.lower().endswith('.pdf'):
            print(f"TOC RAG는 PDF만 지원: {file_name}")
            return
        
        # 실제 TOC 기반 파일 처리 수행
        from rag_toc_based import TOCBasedRAG
        from rag_interface import RAGConfig
        
        print(f"TOC 파일 처리 시작: {file_name}")
        
        # GCS 경로 구성
        gcs_path = f"gs://{bucket}/{file_name}"
        
        # TOC 기반 RAG 설정
        config = RAGConfig(
            storage_type="gcp",
            chunker_type="toc_based",
            embedding_model="openai",
            vector_db_type="postgresql",
            extra_config={
                "bucket_name": bucket,
                "embedding_model": "text-embedding-3-small",
                "table_name": "ideal_answer"
            }
        )
        
        # TOC RAG 시스템으로 처리
        toc_rag = TOCBasedRAG(config)
        results = toc_rag.load_and_process_file(gcs_path)
        
        print(f"TOC 파일 처리 완료: {len(results)}개 결과")
        for i, result in enumerate(results[:3]):  # 처음 3개만 로그
            print(f"결과 {i+1}: {result}")
        
        return f"TOC 파일 처리 완료: {len(results)}개 청크 생성"
        
    except Exception as e:
        print(f"TOC RAG 처리 실패: {str(e)}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        raise
