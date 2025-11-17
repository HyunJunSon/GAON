"""
GCP 스토리지 유틸리티
rag_test/bucket.py 로직 통합
"""
import os
import tempfile
from pathlib import Path
from typing import List, Optional
from google.cloud import storage

from app.core.config import settings


class GCPStorageManager:
    """GCP 스토리지 관리자"""
    
    def __init__(self, bucket_name: Optional[str] = None):
        self.bucket_name = bucket_name or settings.extra_config.get("bucket_name", "gaon-cloud-data")
        self.client = storage.Client()
        self.bucket = self.client.bucket(self.bucket_name)
    
    def download_pdfs_from_prefix(self, prefix: str = "rag-data/pdf변환/") -> List[str]:
        """지정된 prefix에서 PDF 파일들을 임시 디렉토리로 다운로드"""
        temp_dir = Path(tempfile.mkdtemp(prefix="gaon_rag_"))
        downloaded_files = []
        
        blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
        
        for blob in blobs:
            if blob.name.endswith("/") or not blob.name.lower().endswith(".pdf"):
                continue
            
            # 상대 경로 생성
            rel_path = Path(blob.name[len(prefix):])
            dest_path = temp_dir / rel_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 파일 다운로드
            blob.download_to_filename(str(dest_path))
            downloaded_files.append(str(dest_path))
        
        return downloaded_files
    
    def download_single_file(self, blob_path: str) -> str:
        """단일 파일을 임시 위치로 다운로드"""
        blob = self.bucket.blob(blob_path)
        
        # 임시 파일 생성
        suffix = Path(blob_path).suffix
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_path = temp_file.name
        temp_file.close()
        
        # 파일 다운로드
        blob.download_to_filename(temp_path)
        
        return temp_path
    
    def upload_file(self, local_path: str, blob_path: str) -> bool:
        """로컬 파일을 GCP 스토리지에 업로드"""
        try:
            blob = self.bucket.blob(blob_path)
            blob.upload_from_filename(local_path)
            return True
        except Exception:
            return False
    
    def list_files_with_prefix(self, prefix: str) -> List[str]:
        """지정된 prefix의 파일 목록 반환"""
        blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
        return [blob.name for blob in blobs if not blob.name.endswith("/")]
