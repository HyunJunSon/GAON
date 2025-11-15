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
    
    # 📌 블랙리스트 강화: 프롤로그/머리말/처음으로/추천사/에필로그도 제외
    BLACK_TITLES = {
        "차례", "목차", "판권", "표지",
        "프롤로그", "머리말", "추천사",
        "저자 소개", "여는 말",
        "책의 시작", "처음으로",
        "에필로그",
    }
    
    # 📌 정확 일치 블랙리스트 (오탐 방지용)
    NORMALIZE_MAP = {
        "저자소개": "저자 소개",
        "여는말": "여는 말",
    }
    
    def __init__(self, min_chars: int = 600, max_chars: int = 800):
        self.min_chars = min_chars
        self.max_chars = max_chars
    
    def _is_blacklisted(self, title: str) -> bool:
        """제목이 블랙리스트에 포함되는지 확인"""
        if not title:
            return True
            
        # 정규화
        normalized_title = self.NORMALIZE_MAP.get(title.strip(), title.strip())
        
        # 정확 일치 확인
        if normalized_title in self.BLACK_TITLES:
            return True
            
        # 부분 일치 확인 (프롤로그, 머리말 등)
        for black_item in self.BLACK_TITLES:
            if black_item in normalized_title:
                return True
                
        return False
    
    def chunk_pdf_by_toc(self, pdf_path: str, toc_data: List[Dict]) -> List[Dict[str, Any]]:
        """TOC 기반으로 PDF 청킹 (블랙리스트 필터링 포함)"""
        doc = fitz.open(pdf_path)
        
        # 📌 블랙리스트 필터링 적용
        filtered_toc = [entry for entry in toc_data if not self._is_blacklisted(entry.get("title", ""))]
        
        print(f"📋 TOC 필터링: {len(toc_data)} → {len(filtered_toc)} (블랙리스트 {len(toc_data) - len(filtered_toc)}개 제외)")
        
        # TOC 데이터를 계층 구조로 정리
        parent_index, children_index = self._build_parent_index(filtered_toc)
        
        # 리프 노드(최하위 목차)만 추출
        leaf_entries = [entry for entry in filtered_toc if entry["toc_id"] not in children_index]
        
        # 📌 각 섹션의 끝 페이지 계산
        for i, entry in enumerate(leaf_entries):
            start_page = entry["page"]
            # 다음 섹션의 시작 페이지를 찾아서 끝 페이지 결정
            if i + 1 < len(leaf_entries):
                end_page = leaf_entries[i + 1]["page"] - 1
            else:
                end_page = len(doc) - 1  # 마지막 섹션은 문서 끝까지
            
            entry["page_start"] = start_page
            entry["page_end"] = max(start_page, end_page)  # 최소한 시작 페이지와 같거나 큰 값
        
        chunks = []
        for entry in leaf_entries:
            # 해당 섹션의 텍스트 추출
            section_text = self._extract_section_text(doc, entry, filtered_toc)
            
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
        hierarchy = {}
        
        # 현재 항목의 레벨에 따라 적절한 위치에 배치
        current_level = entry["level"]
        level_map = {1: "l1_title", 2: "l2_title", 3: "l3_title"}
        
        # 현재 항목 배치
        if current_level in level_map:
            hierarchy[level_map[current_level]] = entry["title"]
        
        # 부모들을 거슬러 올라가며 계층 구조 구축
        current = entry
        while current["toc_id"] in parent_index:
            parent = parent_index[current["toc_id"]]
            parent_level = parent["level"]
            
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
        # 📌 embed_text 생성: 대제목+중제목+소제목+본문 형식
        title_parts = []
        for level in ["l1_title", "l2_title", "l3_title"]:
            if level in hierarchy and hierarchy[level]:
                title_parts.append(hierarchy[level])
        
        canonical_path = " > ".join(title_parts)
        
        # 📌 embed_text 형식: [canonical_path] full_text
        embed_text = f"[{canonical_path}] {text}" if canonical_path else text
        
        # 📌 book_title을 파일명에서 추출
        book_title = Path(entry.get('book_name', 'Unknown')).stem
        
        return {
            "chunk_id": str(uuid.uuid4()),
            "section_id": entry["toc_id"],
            "canonical_path": canonical_path,
            "chunk_ix": chunk_idx,
            "page_start": entry.get("page_start", entry["page"]),
            "page_end": entry.get("page_end", entry["page"]),
            "full_text": text,
            "embed_text": embed_text.strip(),
            "citation": f"{book_title}, {canonical_path}, p.{entry.get('page_start', entry['page'])}-{entry.get('page_end', entry['page'])}",
            "book_title": book_title,  # 📌 파일명 기반 책 제목
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
