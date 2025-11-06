"""
문서 청킹 전략들
확장성을 고려하여 다양한 문서 형식에 맞는 청킹 전략을 구현
"""
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path

# 로깅 모듈 가져오기
from ..logger import rag_logger

logger = rag_logger


class Chunk:
    """
    청크 정보를 담는 데이터 클래스
    """
    def __init__(self, 
                 content: str, 
                 metadata: Dict[str, Any] = None, 
                 source: str = None, 
                 chunk_index: int = 0):
        self.content = content
        self.metadata = metadata or {}
        self.source = source
        self.chunk_index = chunk_index
    
    def __repr__(self):
        return f"Chunk(source='{self.source}', index={self.chunk_index}, content_len={len(self.content)})"


class BaseChunker(ABC):
    """
    문서 청킹 전략의 추상 베이스 클래스
    """
    
    @abstractmethod
    def chunk(self, text: str, metadata: Dict[str, Any] = None, source: str = None) -> List[Chunk]:
        """
        텍스트를 청킹합니다.
        
        Args:
            text: 청킹할 텍스트
            metadata: 관련 메타데이터 (선택사항)
            source: 소스 식별자 (선택사항)
            
        Returns:
            Chunk 객체의 리스트
        """
        pass


class CharacterChunker(BaseChunker):
    """
    문자 단위로 텍스트를 청킹하는 전략
    """
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 100):
        """
        Args:
            chunk_size: 청크당 최대 문자 수
            overlap: 청크 간 겹치는 문자 수
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, text: str, metadata: Dict[str, Any] = None, source: str = None) -> List[Chunk]:
        """
        텍스트를 문자 단위로 청킹합니다.
        """
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # 텍스트 끝을 넘지 않도록 조정
            if end > len(text):
                end = len(text)
            
            # 청크 생성
            chunk_content = text[start:end]
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                "chunk_start": start,
                "chunk_end": end,
                "chunk_method": "character",
                "chunk_size": len(chunk_content)
            })
            
            chunk = Chunk(
                content=chunk_content,
                metadata=chunk_metadata,
                source=source,
                chunk_index=chunk_index
            )
            chunks.append(chunk)
            
            # 다음 청크 시작 위치 계산 (오버랩 고려)
            start = end - self.overlap
            chunk_index += 1
            
            # 오버랩이 전체 텍스트를 다시 커버하지 않도록 방지
            if start >= end:
                start = end
        
        logger.info(f"문자 단위 청킹 완료: {len(chunks)}개 청크 생성")
        return chunks


class SentenceChunker(BaseChunker):
    """
    문장 단위로 텍스트를 청킹하는 전략
    """
    
    def __init__(self, max_chunk_size: int = 1000, overlap: int = 100):
        """
        Args:
            max_chunk_size: 청크당 최대 문자 수
            overlap: 청크 간 겹치는 문자 수
        """
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
    
    def chunk(self, text: str, metadata: Dict[str, Any] = None, source: str = None) -> List[Chunk]:
        """
        텍스트를 문장 단위로 청킹합니다.
        """
        import re
        
        # 문장 단위로 분할 (마침표, 느낌표, 물음표를 기준으로)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        current_start_pos = 0
        chunk_index = 0
        
        for sentence in sentences:
            # 새 문장이 현재 청크에 추가될 경우의 길이 계산
            candidate_chunk = current_chunk + (" " if current_chunk else "") + sentence
            
            if len(candidate_chunk) <= self.max_chunk_size:
                # 현재 청크에 문장 추가
                current_chunk = candidate_chunk
            else:
                # 현재 청크가 최대 크기를 초과하면 새 청크 생성
                if current_chunk:
                    chunk_metadata = metadata.copy() if metadata else {}
                    chunk_metadata.update({
                        "chunk_start": current_start_pos,
                        "chunk_end": current_start_pos + len(current_chunk),
                        "chunk_method": "sentence",
                        "chunk_size": len(current_chunk)
                    })
                    
                    chunk = Chunk(
                        content=current_chunk,
                        metadata=chunk_metadata,
                        source=source,
                        chunk_index=chunk_index
                    )
                    chunks.append(chunk)
                    
                    # 오버랩 계산: 마지막 n개의 문자를 새 청크의 시작으로 사용
                    if self.overlap > 0:
                        overlap_start = max(0, len(current_chunk) - self.overlap)
                        current_chunk = current_chunk[overlap_start:]
                        current_start_pos = text.find(current_chunk, current_start_pos)
                        chunk_index += 1
                    else:
                        current_chunk = ""
                        current_start_pos = text.find(sentence, current_start_pos + len(current_chunk))
                else:
                    # 문장 자체가 최대 크기를 초과하는 경우 문자 단위 청킹
                    logger.warning(f"문장이 최대 청크 크기보다 큽니다: {sentence[:50]}...")
                    char_chunker = CharacterChunker(chunk_size=self.max_chunk_size, overlap=self.overlap)
                    sub_chunks = char_chunker.chunk(sentence, metadata, source)
                    
                    # 서브 청크의 인덱스를 조정
                    for sub_chunk in sub_chunks:
                        sub_chunk.chunk_index = chunk_index
                        chunks.append(sub_chunk)
                        chunk_index += 1
                    
                    current_chunk = ""
                    current_start_pos = text.find(sentence, current_start_pos) + len(sentence)
        
        # 마지막 청크 처리
        if current_chunk:
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                "chunk_start": current_start_pos,
                "chunk_end": current_start_pos + len(current_chunk),
                "chunk_method": "sentence",
                "chunk_size": len(current_chunk)
            })
            
            chunk = Chunk(
                content=current_chunk,
                metadata=chunk_metadata,
                source=source,
                chunk_index=chunk_index
            )
            chunks.append(chunk)
        
        logger.info(f"문장 단위 청킹 완료: {len(chunks)}개 청크 생성")
        return chunks


class RecursiveCharacterChunker(BaseChunker):
    """
    재귀적 문자 단위 청킹 전략
    여러 분할 기호를 사용하여 의미 있는 단위로 텍스트를 분할
    """
    
    def __init__(self, 
                 chunk_sizes: List[int] = [1000, 500, 200], 
                 separators: List[str] = ["\n\n", "\n", " ", ""],
                 overlap: int = 100):
        """
        Args:
            chunk_sizes: 다양한 청크 크기 (큰 것에서 작은 것으로)
            separators: 분할 기호 리스트 (큰 단위에서 작은 단위로)
            overlap: 청크 간 겹치는 문자 수
        """
        self.chunk_sizes = sorted(chunk_sizes, reverse=True)
        self.separators = separators
        self.overlap = overlap
    
    def chunk(self, text: str, metadata: Dict[str, Any] = None, source: str = None) -> List[Chunk]:
        """
        텍스트를 재귀적 문자 단위로 청킹합니다.
        """
        return self._recursive_chunk(text, self.chunk_sizes[0], metadata, source, 0)
    
    def _recursive_chunk(self, 
                         text: str, 
                         chunk_size: int, 
                         metadata: Dict[str, Any], 
                         source: str, 
                         chunk_index: int) -> List[Chunk]:
        """
        재귀적으로 텍스트를 청킹합니다.
        """
        if len(text) <= chunk_size:
            # 텍스트가 청크 크기보다 작거나 같으면 그대로 청크로 반환
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                "chunk_method": "recursive_character",
                "chunk_size": len(text),
                "max_chunk_size": chunk_size
            })
            
            chunk = Chunk(
                content=text,
                metadata=chunk_metadata,
                source=source,
                chunk_index=chunk_index
            )
            return [chunk]
        
        # 적절한 구분자로 텍스트 분할
        separator = self._get_separator(text)
        splits = text.split(separator)
        
        # 각 분할에 대해 재귀적으로 처리
        chunks = []
        
        current_chunk = ""
        for split in splits:
            # 구분자 포함 여부에 따라 추가
            separator_to_add = separator if current_chunk else ""
            candidate_chunk = current_chunk + separator_to_add + split
            
            if len(candidate_chunk) <= chunk_size:
                current_chunk = candidate_chunk
            else:
                # 현재 청크가 최대 크기를 초과하면 저장하고 새 청크 시작
                if current_chunk:
                    chunk_metadata = metadata.copy() if metadata else {}
                    chunk_metadata.update({
                        "chunk_method": "recursive_character",
                        "max_chunk_size": chunk_size,
                        "separator": separator
                    })
                    
                    chunk = Chunk(
                        content=current_chunk,
                        metadata=chunk_metadata,
                        source=source,
                        chunk_index=chunk_index
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                
                # 오버랩 처리
                if len(split) > chunk_size:
                    # 분할된 텍스트가 여전히 너무 크면 더 작은 청크 크기로 재귀 처리
                    if len(self.chunk_sizes) > 1:
                        smaller_chunker = RecursiveCharacterChunker(
                            chunk_sizes=self.chunk_sizes[1:],
                            separators=self.separators,
                            overlap=self.overlap
                        )
                        sub_chunks = smaller_chunker.chunk(
                            split, 
                            metadata, 
                            source
                        )
                        chunks.extend(sub_chunks)
                        chunk_index += len(sub_chunks)
                    else:
                        # 더 이상 작은 청크 크기가 없으면 현재 청크 크기로 문자 단위 청킹
                        char_chunker = CharacterChunker(
                            chunk_size=chunk_size,
                            overlap=self.overlap
                        )
                        sub_chunks = char_chunker.chunk(
                            split, 
                            metadata, 
                            source
                        )
                        chunks.extend(sub_chunks)
                        chunk_index += len(sub_chunks)
                else:
                    # 오버랩 적용: 이전 청크의 끝부분을 새로운 청크의 시작으로 사용
                    if self.overlap > 0 and chunks:
                        prev_chunk = chunks[-1].content
                        overlap_start = max(0, len(prev_chunk) - self.overlap)
                        current_chunk = prev_chunk[overlap_start:] + separator + split
                    else:
                        current_chunk = split
        
        # 마지막 청크 처리
        if current_chunk:
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                "chunk_method": "recursive_character",
                "max_chunk_size": chunk_size,
                "separator": separator
            })
            
            chunk = Chunk(
                content=current_chunk,
                metadata=chunk_metadata,
                source=source,
                chunk_index=chunk_index
            )
            chunks.append(chunk)
        
        logger.info(f"재귀적 문자 단위 청킹 완료: {len(chunks)}개 청크 생성 (최대 크기: {chunk_size})")
        return chunks
    
    def _get_separator(self, text: str) -> str:
        """
        텍스트에 가장 적절한 구분자를 선택합니다.
        """
        for sep in self.separators:
            if sep in text:
                return sep
        return self.separators[-1]  # 빈 문자열 반환 (문자 단위 분할)


class MarkdownChunker(BaseChunker):
    """
    마크다운 문서에 특화된 청킹 전략
    헤더, 코드 블록 등을 고려하여 청킹
    """
    
    def __init__(self, max_chunk_size: int = 1000, overlap: int = 100):
        """
        Args:
            max_chunk_size: 청크당 최대 문자 수
            overlap: 청크 간 겹치는 문자 수
        """
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
    
    def chunk(self, text: str, metadata: Dict[str, Any] = None, source: str = None) -> List[Chunk]:
        """
        마크다운 문서를 구조에 따라 청킹합니다.
        """
        import re
        
        # 마크다운 헤더로 분할 (h1, h2, h3 등)
        header_pattern = r'\n#{1,6}\s+.*?(?=\n#{1,6}\s+|\Z)'
        sections = re.split(header_pattern, text, flags=re.DOTALL)
        
        # 헤더 정보도 함께 추출
        headers = re.findall(header_pattern, text, flags=re.DOTALL)
        
        chunks = []
        chunk_index = 0
        
        # 첫 번째 섹션(헤더 없이 시작하는 부분) 처리
        if sections and text.startswith(sections[0][:10]):  # 대략적인 확인
            if len(sections[0]) > 0:
                char_chunker = CharacterChunker(
                    chunk_size=self.max_chunk_size,
                    overlap=self.overlap
                )
                sub_chunks = char_chunker.chunk(
                    sections[0], 
                    metadata, 
                    source
                )
                
                for sub_chunk in sub_chunks:
                    sub_chunk.chunk_index = chunk_index
                    chunks.append(sub_chunk)
                    chunk_index += 1
            sections = sections[1:]
        
        # 나머지 섹션(각각 헤더를 포함하는) 처리
        for header, section in zip(headers, sections):
            section_with_header = header + section
            
            if len(section_with_header) <= self.max_chunk_size:
                # 섹션이 청크 크기보다 작으면 그대로 청크로 추가
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update({
                    "chunk_method": "markdown",
                    "header": header.strip(),
                    "chunk_size": len(section_with_header)
                })
                
                chunk = Chunk(
                    content=section_with_header,
                    metadata=chunk_metadata,
                    source=source,
                    chunk_index=chunk_index
                )
                chunks.append(chunk)
                chunk_index += 1
            else:
                # 섹션이 너무 크면 재귀적 청킹
                recursive_chunker = RecursiveCharacterChunker(
                    chunk_sizes=[self.max_chunk_size, 500, 200],
                    separators=["\n\n", "\n", " ", ""],
                    overlap=self.overlap
                )
                sub_chunks = recursive_chunker.chunk(
                    section_with_header, 
                    metadata, 
                    source
                )
                
                for sub_chunk in sub_chunks:
                    sub_chunk.chunk_index = chunk_index
                    chunks.append(sub_chunk)
                    chunk_index += 1
    
        logger.info(f"마크다운 청킹 완료: {len(chunks)}개 청크 생성")
        return chunks


class ChunkerFactory:
    """
    청킹 전략을 생성하는 팩토리 클래스
    """
    
    def __init__(self):
        self.chunkers = {
            'character': CharacterChunker(),
            'sentence': SentenceChunker(),
            'recursive': RecursiveCharacterChunker(),
            'markdown': MarkdownChunker(),
        }
    
    def register_chunker(self, name: str, chunker: BaseChunker) -> None:
        """
        새 청킹 전략을 등록합니다.
        
        Args:
            name: 청커 이름
            chunker: BaseChunker 인스턴스
        """
        self.chunkers[name] = chunker
    
    def get_chunker(self, chunker_type: str, **kwargs) -> BaseChunker:
        """
        지정된 유형의 청킹 전략을 반환합니다.
        
        Args:
            chunker_type: 청킹 전략 유형
            **kwargs: 청커 초기화에 필요한 추가 인자
            
        Returns:
            BaseChunker 인스턴스
        """
        if chunker_type in self.chunkers:
            # 기존 청커의 클래스를 사용하여 새 인스턴스 생성 (kwargs 적용)
            chunker_class = self.chunkers[chunker_type].__class__
            return chunker_class(**kwargs)
        else:
            raise ValueError(f"지원되지 않는 청킹 유형입니다: {chunker_type}")
    
    def chunk_by_format(self, text: str, file_format: str, metadata: Dict[str, Any] = None, 
                        source: str = None, **kwargs) -> List[Chunk]:
        """
        파일 형식에 따라 적절한 청킹 전략을 선택하여 텍스트를 청킹합니다.
        
        Args:
            text: 청킹할 텍스트
            file_format: 파일 형식 (예: 'pdf', 'epub', 'txt', 'md')
            metadata: 관련 메타데이터 (선택사항)
            source: 소스 식별자 (선택사항)
            **kwargs: 청킹 전략에 전달할 추가 인자
            
        Returns:
            Chunk 객체의 리스트
        """
        # 파일 형식에 따라 청킹 전략 선택
        if file_format.lower() in ['.md', '.markdown']:
            chunker_type = 'markdown'
        elif file_format.lower() in ['.pdf', '.epub']:
            # PDF와 EPUB은 일반적으로 구조화된 텍스트이므로 재귀적 청킹이 효과적
            chunker_type = 'recursive'
        else:
            # 기본 청킹 전략
            chunker_type = 'recursive'
        
        chunker = self.get_chunker(chunker_type, **kwargs)
        return chunker.chunk(text, metadata, source)