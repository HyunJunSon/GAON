import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
from urllib.parse import urlparse
import logging

# 로깅 모듈 가져오기
from ..logger import rag_logger

logger = rag_logger


class Document:
    """
    문서의 내용, 메타데이터 및 소스 정보를 나타내는 클래스
    """
    def __init__(self, 
                 content: str, 
                 metadata: Dict[str, Any], 
                 source: str = None, 
                 doc_type: str = None):
        self.content = content
        self.metadata = metadata
        self.source = source
        self.doc_type = doc_type
        
    def __repr__(self):
        return f"Document(source='{self.source}', doc_type='{self.doc_type}', content_len={len(self.content)})"


class BaseLoader(ABC):
    """
    문서 로더를 위한 추상 베이스 클래스
    """
    
    @abstractmethod
    def load(self, source: str) -> List[Document]:
        """
        주어진 소스에서 문서를 로드합니다.
        
        Args:
            source: 문서를 로드할 소스 (경로, URL 또는 식별자)
            
        Returns:
            Document 객체의 리스트
        """
        pass


class LocalFileLoader(BaseLoader):
    """
    다양한 형식을 지원하는 로컬 파일 로더
    """
    
    def __init__(self):
        # 선택적 종속성을 위한 메서드 내부 가져오기
        try:
            import pypdf
        except ImportError:
            pypdf = None
        self._pypdf = pypdf
        
        try:
            from ebooklib import epub
            import bs4
        except ImportError:
            epub = None
            bs4 = None
        self._epub_lib = epub
        self._bs4 = bs4
    
    def load(self, source: str) -> List[Document]:
        """
        로컬 파일 경로에서 문서를 로드합니다.
        
        Args:
            source: 로컬 파일의 경로
            
        Returns:
            Document 객체의 리스트
        """
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"파일이 존재하지 않습니다: {source}")
        
        extension = path.suffix.lower()
        
        if extension == '.pdf':
            return self._load_pdf(source)
        elif extension == '.epub':
            return self._load_epub(source)
        else:
            # 다른 텍스트 기반 형식
            return self._load_text_file(source)
    
    def _load_pdf(self, file_path: str) -> List[Document]:
        """
        PDF 파일에서 문서를 로드합니다.
        """
        if not self._pypdf:
            raise ImportError("PDF 파일 로드에는 pypdf가 필요합니다. 'pip install pypdf'로 설치하세요.")
        
        try:
            import pypdf
            documents = []
            
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text() + "\n"
                
                doc = Document(
                    content=content,
                    metadata={
                        "source": file_path,
                        "file_type": "pdf",
                        "pages": len(pdf_reader.pages),
                        "title": os.path.basename(file_path)
                    },
                    source=file_path,
                    doc_type="pdf"
                )
                documents.append(doc)
                
            logger.info(f"PDF에서 {len(documents)}개 문서 로드 완료: {file_path}")
            return documents
        except Exception as e:
            logger.error(f"PDF 파일 로드 오류 {file_path}: {str(e)}")
            raise
    
    def _load_epub(self, file_path: str) -> List[Document]:
        """
        EPUB 파일에서 문서를 로드합니다.
        """
        if not self._epub_lib or not self._bs4:
            raise ImportError("EPUB 파일 로드에는 ebooklib과 beautifulsoup4가 필요합니다. "
                            "'pip install ebooklib beautifulsoup4'로 설치하세요.")
        
        try:
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
            
            documents = []
            
            book = epub.read_epub(file_path)
            
            content = ""
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    content += soup.get_text() + "\n"
            
            doc = Document(
                content=content,
                metadata={
                    "source": file_path,
                    "file_type": "epub",
                    "title": book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else os.path.basename(file_path),
                    "author": book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else "Unknown"
                },
                source=file_path,
                doc_type="epub"
            )
            documents.append(doc)
            
            logger.info(f"EPUB에서 {len(documents)}개 문서 로드 완료: {file_path}")
            return documents
        except Exception as e:
            logger.error(f"EPUB 파일 로드 오류 {file_path}: {str(e)}")
            raise
    
    def _load_text_file(self, file_path: str) -> List[Document]:
        """
        텍스트 기반 파일에서 문서를 로드합니다 (txt, md 등).
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            doc = Document(
                content=content,
                metadata={
                    "source": file_path,
                    "file_type": Path(file_path).suffix.lower(),
                    "title": os.path.basename(file_path)
                },
                source=file_path,
                doc_type="text"
            )
            
            logger.info(f"텍스트 파일에서 1개 문서 로드 완료: {file_path}")
            return [doc]
        except Exception as e:
            logger.error(f"텍스트 파일 로드 오류 {file_path}: {str(e)}")
            raise


class DocumentLoader:
    """
    로딩 프로세스를 추상화하는 주요 문서 로더 클래스.
    다양한 파일 소스 및 형식을 지원합니다.
    """
    
    def __init__(self, storage_adapter=None):
        self.local_file_loader = LocalFileLoader()
        self.storage_adapter = storage_adapter
    
    def load_documents(self, source: str) -> List[Document]:
        """
        지정된 소스에서 문서를 로드합니다.
        
        Args:
            source: 문서를 로드할 소스. 다음을 포함할 수 있습니다:
                    - 로컬 파일 경로
                    - GCS 경로 (gs://bucket/path)
                    - URL (미구현)
                    
        Returns:
            Document 객체의 리스트
        """
        # GCS 경로인지 확인
        if source.startswith('gs://'):
            if not self.storage_adapter:
                raise ValueError("GCS 파일 로딩을 위해 storage_adapter가 필요합니다")
            
            # 임시 파일로 다운로드
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(source).suffix) as tmp_file:
                temp_path = tmp_file.name
            
            try:
                # GCS에서 파일 다운로드
                self.storage_adapter.download_file(source, temp_path)
                # 로컬 파일로 로드
                documents = self.local_file_loader.load(temp_path)
                # 소스 정보 업데이트
                for doc in documents:
                    doc.source = source
                return documents
            finally:
                # 임시 파일 정리
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        
        # 로컬 파일 경로인지 확인
        elif os.path.exists(source) or Path(source).exists():
            return self.local_file_loader.load(source)
        else:
            # URL인지 확인
            parsed = urlparse(source)
            if parsed.scheme in ['http', 'https']:
                raise NotImplementedError("URL 로딩은 아직 구현되지 않았습니다")
            else:
                raise NotImplementedError(f"지원되지 않는 소스 형식입니다: {source}")