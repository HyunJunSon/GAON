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
        
        # 리팩토링 후: 파일 처리는 더 이상 필요하지 않음
        # TOC 기반 RAG는 검색 전용으로 변경됨
        print(f"TOC RAG 리팩토링 완료: 파일 처리는 더 이상 수행하지 않습니다 - {file_name}")
        print("파일 처리 로직이 제거되었습니다. 검색 전용 RAG로 변경되었습니다.")
        
        return "TOC RAG 리팩토링 완료: 파일 처리 로직 제거됨"
        
    except Exception as e:
        print(f"TOC RAG 처리 실패: {str(e)}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        raise
