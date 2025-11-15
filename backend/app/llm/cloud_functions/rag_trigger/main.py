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
        
        # 실제 파일 처리 수행
        from rag_auto_selector import process_file_with_auto_rag
        
        print(f"파일 처리 시작: {file_name}")
        
        # GCS 경로 구성
        gcs_path = f"gs://{bucket}/{file_name}"
        
        # RAG 자동 선택 시스템으로 처리
        results = process_file_with_auto_rag(gcs_path)
        
        print(f"파일 처리 완료: {len(results)}개 결과")
        for i, result in enumerate(results[:3]):  # 처음 3개만 로그
            print(f"결과 {i+1}: {result}")
        
        return f"파일 처리 완료: {len(results)}개 청크 생성"
        
    except Exception as e:
        print(f"RAG 처리 실패: {str(e)}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        raise
