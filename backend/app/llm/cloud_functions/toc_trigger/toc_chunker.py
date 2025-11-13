"""
TOC 기반 청킹 유틸리티
rag_test/chunking.py 로직 통합
"""
import json
import uuid
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Tuple, Any
import fitz


class TOCChunker:
    """TOC 기반 청킹 처리기"""
    
    def __init__(self, min_chars: int = 600, max_chars: int = 800):
        self.min_chars = min_chars
        self.max_chars = max_chars
    
    def chunk_pdf_by_toc(self, pdf_path: str, toc_data: List[Dict]) -> List[Dict[str, Any]]:
        """TOC 기반으로 PDF 청킹"""
        doc = fitz.open(pdf_path)
        
        # TOC 데이터를 계층 구조로 정리
        parent_index, children_index = self._build_parent_index(toc_data)
        
        # 리프 노드(최하위 목차)만 추출
        leaf_entries = [entry for entry in toc_data if entry["toc_id"] not in children_index]
        
        chunks = []
        for entry in leaf_entries:
            # 해당 섹션의 텍스트 추출
            section_text = self._extract_section_text(doc, entry, toc_data)
            
            if not section_text.strip():
                continue
            
            # 계층 구조 정보 생성
            hierarchy = self._build_hierarchy(entry, parent_index)
            
            # 청킹 수행
            section_chunks = self._chunk_text(section_text, entry, hierarchy)
            chunks.extend(section_chunks)
        
        doc.close()
        return chunks
    
    def _build_parent_index(self, toc_data: List[Dict]) -> Tuple[Dict[str, Dict], Dict[str, List[Dict]]]:
        """부모-자식 관계 인덱스 구축"""
        parent_index = {}
        children_index = {}
        
        for i, entry in enumerate(toc_data):
            entry_id = entry["toc_id"]
            level = entry["level"]
            
            # 부모 찾기
            parent = None
            for j in range(i - 1, -1, -1):
                if toc_data[j]["level"] < level:
                    parent = toc_data[j]
                    break
            
            if parent:
                parent_id = parent["toc_id"]
                parent_index[entry_id] = parent
                
                if parent_id not in children_index:
                    children_index[parent_id] = []
                children_index[parent_id].append(entry)
        
        return parent_index, children_index
    
    def _extract_section_text(self, doc: fitz.Document, entry: Dict, toc_data: List[Dict]) -> str:
        """섹션 텍스트 추출"""
        start_page = entry["page"] - 1  # 0-based
        
        # 다음 섹션의 시작 페이지 찾기
        end_page = len(doc) - 1
        current_level = entry["level"]
        
        for other in toc_data:
            if (other["page"] > entry["page"] and 
                other["level"] <= current_level):
                end_page = other["page"] - 2  # 이전 페이지까지
                break
        
        # 텍스트 추출
        text_parts = []
        for page_num in range(max(0, start_page), min(len(doc), end_page + 1)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                text_parts.append(text)
        
        return "\n\n".join(text_parts)
    
    def _build_hierarchy(self, entry: Dict, parent_index: Dict[str, Dict]) -> Dict[str, str]:
        """계층 구조 정보 생성"""
        hierarchy = {"l3_title": entry["title"]}  # 현재 레벨을 L3로 가정
        
        # 부모들을 거슬러 올라가며 계층 구조 구축
        current = entry
        level_map = {3: "l3_title", 2: "l2_title", 1: "l1_title"}
        
        while current["toc_id"] in parent_index:
            parent = parent_index[current["toc_id"]]
            parent_level = min(parent["level"], 2)  # L1, L2로 제한
            
            if parent_level in level_map:
                hierarchy[level_map[parent_level]] = parent["title"]
            
            current = parent
        
        return hierarchy
    
    def _chunk_text(self, text: str, entry: Dict, hierarchy: Dict[str, str]) -> List[Dict[str, Any]]:
        """텍스트를 청크로 분할"""
        text = self._norm_text(text)
        
        if len(text) <= self.max_chars:
            # 단일 청크
            return [self._create_chunk(text, entry, hierarchy, 0)]
        
        # 여러 청크로 분할
        chunks = []
        sentences = re.split(r'[.!?]\s+', text)
        
        current_chunk = ""
        chunk_idx = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 청크 크기 확인
            potential_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            if len(potential_chunk) > self.max_chars and len(current_chunk) >= self.min_chars:
                # 현재 청크 저장
                chunks.append(self._create_chunk(current_chunk, entry, hierarchy, chunk_idx))
                current_chunk = sentence
                chunk_idx += 1
            else:
                current_chunk = potential_chunk
        
        # 마지막 청크 저장
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, entry, hierarchy, chunk_idx))
        
        return chunks
    
    def _create_chunk(self, text: str, entry: Dict, hierarchy: Dict[str, str], chunk_idx: int) -> Dict[str, Any]:
        """청크 데이터 생성"""
        # embed_text 생성 (계층 구조 + 본문)
        path_parts = []
        for level in ["l1_title", "l2_title", "l3_title"]:
            if level in hierarchy and hierarchy[level]:
                path_parts.append(hierarchy[level])
        
        canonical_path = " > ".join(path_parts)
        embed_text = f"[{canonical_path}] {text}" if canonical_path else text
        
        return {
            "chunk_id": str(uuid.uuid4()),
            "section_id": entry["toc_id"],
            "canonical_path": canonical_path,
            "chunk_ix": chunk_idx,
            "page_start": entry["page"],
            "page_end": entry["page"],  # 단순화
            "full_text": text,
            "embed_text": embed_text.strip(),
            "citation": f"{entry['book_name']}, p.{entry['page']}",
            **hierarchy
        }
    
    def _norm_text(self, s: str, max_len: int = None) -> str:
        """텍스트 정규화"""
        if s is None:
            return ""
        
        s = unicodedata.normalize("NFKC", s)
        s = re.sub(r"\s+", " ", s).strip()
        s = s.replace(""", '"').replace(""", '"').replace("'", "'").replace("'", "'")
        
        if max_len:
            s = s[:max_len]
        
        return s
