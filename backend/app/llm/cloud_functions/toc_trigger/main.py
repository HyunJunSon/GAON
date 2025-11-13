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
        
        # TOC 기반 RAG 시스템 import 및 실행
        from rag_auto_selector import get_rag_auto_selector
        from rag_manager import RAGType
        
        # TOC 기반 RAG로 강제 설정
        selector = get_rag_auto_selector()
        rag = selector.manager.switch_to(RAGType.TOC_BASED)
        
        # 파일 처리
        gcs_path = f"gs://{bucket}/{file_name}"
        results = rag.load_and_process_file(gcs_path)
        
        # 결과 분석
        success_count = sum(1 for r in results if r.get('status') == 'success')
        error_count = len(results) - success_count
        
        print(f"TOC RAG 처리 완료: {file_name}")
        print(f"목차 기반 청킹 - 성공: {success_count}개, 실패: {error_count}개")
        
        return f"TOC 처리 성공: {success_count}/{len(results)}개 청크"
        
    except Exception as e:
        print(f"TOC RAG 처리 실패: {str(e)}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        raise
