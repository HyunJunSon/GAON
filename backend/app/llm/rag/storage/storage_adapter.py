"""
스토리지 어댑터 시스템
GCP 스토리지 및 기타 소스에서 문서를 가져오기 위한 확장 가능한 시스템
"""
import os
import tempfile
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from urllib.parse import urlparse

# 로깅 모듈 가져오기
from ..logger import rag_logger

logger = rag_logger


class StorageAdapter(ABC):
    """
    문서 스토리지 어댑터의 추상 베이스 클래스
    다양한 스토리지 시스템을 지원하기 위한 인터페이스
    """
    
    @abstractmethod
    def download_file(self, source_identifier: str, destination_path: str) -> str:
        """
        스토리지에서 파일을 다운로드합니다.
        
        Args:
            source_identifier: 소스 식별자 (URL, 버킷 경로 등)
            destination_path: 다운로드할 로컬 경로
            
        Returns:
            실제 다운로드된 파일의 경로
        """
        pass
    
    @abstractmethod
    def list_files(self, source_path: str) -> List[str]:
        """
        스토리지에서 파일 목록을 가져옵니다.
        
        Args:
            source_path: 소스 경로
            
        Returns:
            파일 식별자 목록
        """
        pass
    
    @abstractmethod
    def file_exists(self, source_identifier: str) -> bool:
        """
        스토리지에 파일이 존재하는지 확인합니다.
        
        Args:
            source_identifier: 소스 식별자
            
        Returns:
            파일 존재 여부
        """
        pass


class LocalStorageAdapter(StorageAdapter):
    """
    로컬 파일 시스템을 위한 스토리지 어댑터
    """
    
    def download_file(self, source_identifier: str, destination_path: str) -> str:
        """
        로컬 파일을 지정된 경로로 복사합니다.
        """
        source_path = Path(source_identifier)
        dest_path = Path(destination_path)
        
        if not source_path.exists():
            raise FileNotFoundError(f"소스 파일이 존재하지 않습니다: {source_identifier}")
        
        # 디렉토리 생성
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 파일 복사
        import shutil
        shutil.copy2(str(source_path), str(dest_path))
        
        logger.info(f"로컬 파일 복사 완료: {source_identifier} -> {destination_path}")
        return str(dest_path)
    
    def list_files(self, source_path: str) -> List[str]:
        """
        로컬 디렉토리에서 파일 목록을 가져옵니다.
        """
        path = Path(source_path)
        if not path.exists() or not path.is_dir():
            return []
        
        files = [str(file_path) for file_path in path.rglob('*') if file_path.is_file()]
        logger.info(f"로컬 디렉토리에서 {len(files)}개 파일을 찾았습니다: {source_path}")
        return files
    
    def file_exists(self, source_identifier: str) -> bool:
        """
        로컬 파일이 존재하는지 확인합니다.
        """
        return Path(source_identifier).exists()


class GCPStorageAdapter(StorageAdapter):
    """
    GCP 스토리지용 스토리지 어댑터
    """
    
    def __init__(self, bucket_name: str = None, credentials_path: str = None):
        """
        GCP 스토리지 어댑터 초기화
        
        Args:
            bucket_name: GCP 버킷 이름
            credentials_path: 서비스 계정 키 파일 경로 (선택사항)
        """
        self.bucket_name = bucket_name
        
        try:
            from google.cloud import storage
            self._storage_client = storage.Client.from_service_account_json(credentials_path) if credentials_path else storage.Client()
        except ImportError:
            raise ImportError("GCP 스토리지 사용을 위해 'google-cloud-storage' 패키지를 설치해야 합니다: "
                            "pip install google-cloud-storage")
    
    def download_file(self, source_identifier: str, destination_path: str) -> str:
        """
        GCP 스토리지에서 파일을 다운로드합니다.
        
        Args:
            source_identifier: GCS 객체 경로 (버킷/파일 경로 형식 또는 파일 경로)
            destination_path: 다운로드할 로컬 경로
        """
        from urllib.parse import unquote
        
        # source_identifier에서 버킷 이름과 객체 이름 분리
        if source_identifier.startswith('gs://'):
            # gs://bucket_name/path/to/file 형식
            _, path = source_identifier.split('gs://', 1)
            bucket_name, blob_name = path.split('/', 1)
        elif self.bucket_name:
            # 버킷 이름이 인스턴스에서 지정된 경우
            bucket_name = self.bucket_name
            # GCS 클라이언트 내부에서 URL 인코딩을 처리하므로 원본 경로 사용
            blob_name = source_identifier.lstrip('/')
        else:
            # 인스턴스에도 버킷 이름이 없을 경우 예외 발생
            raise ValueError("GCS 경로에 버킷 이름이 포함되어야 하거나, 어댑터에 버킷 이름이 지정되어야 합니다.")
        
        try:
            bucket = self._storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            # 다운로드 디렉토리 생성
            dest_path = Path(destination_path)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 파일 다운로드
            blob.download_to_filename(str(dest_path))
            
            logger.info(f"GCP 스토리지에서 파일 다운로드 완료: {source_identifier} -> {destination_path}")
            return str(dest_path)
        except Exception as e:
            logger.error(f"GCP 스토리지에서 파일 다운로드 실패 {source_identifier}: {str(e)}")
            raise
    
    def list_files(self, source_path: str) -> List[str]:
        """
        GCP 스토리지에서 파일 목록을 가져옵니다.
        
        Args:
            source_path: GCS 디렉토리 경로
        """
        if self.bucket_name is None:
            raise ValueError("버킷 이름이 지정되지 않았습니다.")
        
        try:
            bucket = self._storage_client.bucket(self.bucket_name)
            # source_path를 접두사로 사용하여 해당 경로의 파일만 나열
            prefix = source_path.lstrip('/') if source_path != '/' else None
            blobs = bucket.list_blobs(prefix=prefix)
            
            # GCS 경로 형식으로 파일 목록 반환
            file_list = [f"gs://{self.bucket_name}/{blob.name}" for blob in blobs if not blob.name.endswith('/')]
            
            logger.info(f"GCP 스토리지에서 {len(file_list)}개 파일을 찾았습니다: gs://{self.bucket_name}/{prefix or ''}")
            return file_list
        except Exception as e:
            logger.error(f"GCP 스토리지에서 파일 목록 가져오기 실패 {source_path}: {str(e)}")
            raise
    
    def file_exists(self, source_identifier: str) -> bool:
        """
        GCP 스토리지에 파일이 존재하는지 확인합니다.
        
        Args:
            source_identifier: GCS 객체 경로
        """
        # source_identifier에서 버킷 이름과 객체 이름 분리
        if source_identifier.startswith('gs://'):
            _, path = source_identifier.split('gs://', 1)
            bucket_name, blob_name = path.split('/', 1)
        elif self.bucket_name:
            bucket_name = self.bucket_name
            # GCS 클라이언트 내부에서 URL 인코딩을 처리하므로 원본 경로 사용
            blob_name = source_identifier.lstrip('/')
        else:
            raise ValueError("GCS 경로에 버킷 이름이 포함되어야 하거나, 어댑터에 버킷 이름이 지정되어야 합니다.")
        
        try:
            bucket = self._storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            return blob.exists()
        except Exception as e:
            logger.error(f"GCP 스토리지에서 파일 존재 확인 실패 {source_identifier}: {str(e)}")
            raise


class S3StorageAdapter(StorageAdapter):
    """
    AWS S3용 스토리지 어댑터 (미구현 - 예시용)
    """
    
    def __init__(self, bucket_name: str = None, region_name: str = None, 
                 access_key: str = None, secret_key: str = None):
        """
        AWS S3 스토리지 어댑터 초기화
        
        Args:
            bucket_name: S3 버킷 이름
            region_name: AWS 리전 이름
            access_key: AWS 액세스 키 (선택사항)
            secret_key: AWS 시크릿 키 (선택사항)
        """
        self.bucket_name = bucket_name
        self.region_name = region_name
        
        try:
            import boto3
            if access_key and secret_key:
                self._s3_client = boto3.client(
                    's3',
                    region_name=region_name,
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key
                )
            else:
                # 자격 증명이 제공되지 않은 경우 기본 자격 증명 사용
                self._s3_client = boto3.client('s3', region_name=region_name)
        except ImportError:
            raise ImportError("AWS S3 사용을 위해 'boto3' 패키지를 설치해야 합니다: pip install boto3")
    
    def download_file(self, source_identifier: str, destination_path: str) -> str:
        """
        AWS S3에서 파일을 다운로드합니다.
        """
        raise NotImplementedError("S3 스토리지 어댑터는 아직 구현되지 않았습니다. 확장성을 위해 예시만 제공합니다.")
    
    def list_files(self, source_path: str) -> List[str]:
        """
        AWS S3에서 파일 목록을 가져옵니다.
        """
        raise NotImplementedError("S3 스토리지 어댑터는 아직 구현되지 않았습니다. 확장성을 위해 예시만 제공합니다.")
    
    def file_exists(self, source_identifier: str) -> bool:
        """
        AWS S3에 파일이 존재하는지 확인합니다.
        """
        raise NotImplementedError("S3 스토리지 어댑터는 아직 구현되지 않았습니다. 확장성을 위해 예시만 제공합니다.")


class StorageAdapterFactory:
    """
    스토리지 어댑터를 생성하는 팩토리 클래스
    """
    
    def __init__(self):
        self.adapters = {}
    
    def register_adapter(self, name: str, adapter_class) -> None:
        """
        새 스토리지 어댑터를 등록합니다.
        
        Args:
            name: 어댑터 이름
            adapter_class: 어댑터 클래스
        """
        self.adapters[name] = adapter_class
    
    def get_adapter(self, storage_type: str, **kwargs) -> StorageAdapter:
        """
        지정된 유형의 스토리지 어댑터를 반환합니다.
        
        Args:
            storage_type: 스토리지 유형 (예: 'gcp', 'local', 's3')
            **kwargs: 어댑터 초기화에 필요한 추가 인자
            
        Returns:
            StorageAdapter 인스턴스
        """
        if storage_type == 'gcp':
            return GCPStorageAdapter(
                bucket_name=kwargs.get('bucket_name'),
                credentials_path=kwargs.get('credentials_path')
            )
        elif storage_type == 'local':
            return LocalStorageAdapter()
        elif storage_type == 's3':
            return S3StorageAdapter(
                bucket_name=kwargs.get('bucket_name'),
                region_name=kwargs.get('region_name'),
                access_key=kwargs.get('access_key'),
                secret_key=kwargs.get('secret_key')
            )
        else:
            raise ValueError(f"지원되지 않는 스토리지 유형입니다: {storage_type}")