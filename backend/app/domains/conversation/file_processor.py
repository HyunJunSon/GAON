import os
import uuid
from typing import BinaryIO, Tuple
from google.cloud import storage
from pypdf import PdfReader
from docx import Document
import io


class FileProcessor:
    def __init__(self, bucket_name: str = "gaon-cloud-data"):
        self.bucket_name = bucket_name
        self.base_path = "user-upload-conv-data"  # 기본 경로
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    def validate_file_content(self, file_content: bytes, file_type: str) -> bool:
        """파일 내용 유효성 검사"""
        try:
            if file_type == "pdf":
                PdfReader(io.BytesIO(file_content))
            elif file_type == "docx":
                Document(io.BytesIO(file_content))
            elif file_type == "txt":
                file_content.decode('utf-8')
            return True
        except Exception:
            return False

    def extract_text(self, file_content: bytes, file_type: str) -> str:
        """파일에서 텍스트 추출"""
        try:
            if file_type == "txt":
                return file_content.decode('utf-8')
            
            elif file_type == "pdf":
                reader = PdfReader(io.BytesIO(file_content))
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
            
            elif file_type == "docx":
                doc = Document(io.BytesIO(file_content))
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text.strip()
            
            return ""
        except Exception as e:
            raise ValueError(f"텍스트 추출 실패: {str(e)}")

    def upload_to_gcs(self, file_content: bytes, user_id: int, original_filename: str) -> str:
        """GCS에 파일 업로드 (폴더는 자동 생성됨)"""
        try:
            # 고유한 파일 경로 생성
            file_id = str(uuid.uuid4())
            file_extension = original_filename.split('.')[-1].lower()
            # 경로: user-upload-conv-data/conversations/user_123/uuid.txt
            gcs_path = f"{self.base_path}/conversations/user_{user_id}/{file_id}.{file_extension}"
            
            # GCS에 업로드 (폴더 구조는 자동으로 생성됨)
            blob = self.bucket.blob(gcs_path)
            blob.upload_from_string(file_content)
            
            return gcs_path
        except Exception as e:
            raise ValueError(f"GCS 업로드 실패: {str(e)}")

    def delete_from_gcs(self, gcs_path: str) -> bool:
        """GCS에서 파일 삭제"""
        try:
            blob = self.bucket.blob(gcs_path)
            blob.delete()
            return True
        except Exception:
            return False