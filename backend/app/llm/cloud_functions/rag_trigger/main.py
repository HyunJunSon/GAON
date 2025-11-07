import functions_framework
import os
import sys
import tempfile
import logging

@functions_framework.cloud_event
def rag_file_processor(cloud_event):
    """RAG 시스템으로 GCS 파일 처리"""
    
    try:
        # Pub/Sub 메시지에서 정보 추출
        message = cloud_event.data.get('message', {})
        attributes = message.get('attributes', {})
        
        bucket = attributes.get('bucketId')
        file_name = attributes.get('objectId')
        event_type = attributes.get('eventType')
        
        print(f"RAG 처리 시작: {file_name}")
        
        # rag-data 경로만 처리
        if not file_name or not file_name.startswith('rag-data/'):
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
        
        # RAG 시스템 import 및 실행
        from rag import RAGSystem
        
        # RAG 시스템 초기화
        rag_system = RAGSystem(
            storage_type="gcp",
            bucket_name=bucket
        )
        
        # 파일 처리
        results = rag_system.load_and_process_from_storage(
            storage_path=file_name
        )
        
        print(f"RAG 처리 완료: {file_name}, {len(results)}개 청크 처리됨")
        return f"성공: {len(results)}개 청크 처리"
        
    except Exception as e:
        print(f"RAG 처리 실패: {str(e)}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        raise
