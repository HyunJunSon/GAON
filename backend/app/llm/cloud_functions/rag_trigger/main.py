import functions_framework
import os
import sys
import tempfile
import logging

@functions_framework.cloud_event
def rag_file_processor(cloud_event):
    """RAG 자동 선택 시스템으로 GCS 파일 처리"""
    
    try:
        # Pub/Sub 메시지에서 정보 추출
        message = cloud_event.data.get('message', {})
        attributes = message.get('attributes', {})
        
        bucket = attributes.get('bucketId')
        file_name = attributes.get('objectId')
        event_type = attributes.get('eventType')
        
        print(f"RAG 자동 처리 시작: {file_name}")
        
        # rag-data/documents 경로만 처리 (toc-pdfs 제외)
        if not file_name or not file_name.startswith('rag-data/documents/'):
            print(f"RAG 처리 제외: {file_name}")
            return
        
        # 파일 생성 이벤트만 처리
        if event_type != 'OBJECT_FINALIZE':
            print(f"처리하지 않는 이벤트: {event_type}")
            return
        
        # 지원 파일 형식 확인
        supported_exts = ['.pdf', '.epub', '.txt', '.docx', '.md']
        if not any(file_name.lower().endswith(ext) for ext in supported_exts):
            print(f"지원하지 않는 파일 형식: {file_name}")
            return
        
        # 리팩토링 후: 파일 처리는 더 이상 필요하지 않음
        # Legacy RAG는 검색 전용으로 변경됨
        print(f"Legacy RAG 리팩토링 완료: 파일 처리는 더 이상 수행하지 않습니다 - {file_name}")
        print("파일 처리 로직이 제거되었습니다. 검색 전용 RAG로 변경되었습니다.")
        
        return "Legacy RAG 리팩토링 완료: 파일 처리 로직 제거됨"
        
    except Exception as e:
        print(f"RAG 처리 실패: {str(e)}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        raise
