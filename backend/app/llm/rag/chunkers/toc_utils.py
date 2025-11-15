"""
TOC(목차) 추출 및 처리 유틸리티
rag_test/toc_extract.py 로직 통합
"""
import json
import uuid
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Any
import fitz  # pymupdf


class TOCExtractor:
    """PDF 목차 추출기"""
    
    # 블랙리스트 제목들
    BLACK_TITLES = {
        "차례", "목차", "판권", "표지",
        "프롤로그", "머리말", "추천사",
        "저자 소개", "여는 말",
        "책의 시작", "처음으로",
    }
    
    NORMALIZE_MAP = {
        "저자소개": "저자 소개",
        "여는말": "여는 말",
    }
    
    def __init__(self):
        self.safe_pattern = re.compile(r'[\\/:*?"<>|]+')
    
    def extract_toc_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """PDF에서 목차 추출"""
        try:
            print(f"[DEBUG] PDF 파일 열기 시도: {pdf_path}")
            doc = fitz.open(pdf_path)
            print(f"[DEBUG] PDF 문서 열기 성공, 페이지 수: {doc.page_count}")
            
            toc = doc.get_toc()
            print(f"[DEBUG] TOC 추출 결과: {len(toc) if toc else 0}개 항목")
            
            if toc:
                print(f"[DEBUG] 첫 번째 TOC 항목 예시: {toc[0] if toc else 'None'}")
            
            doc.close()
            
            if not toc:
                print("[DEBUG] TOC가 비어있음 - 빈 리스트 반환")
                return []
            
            results = []
            for i, (level, title, page) in enumerate(toc):
                print(f"[DEBUG] TOC 항목 {i}: level={level}, title='{title}', page={page}")
                
                if self._is_blacklisted_title(title):
                    print(f"[DEBUG] 블랙리스트 제목으로 스킵: '{title}'")
                    continue
                
                normalized_title = self._norm_title(title)
                if not normalized_title:
                    print(f"[DEBUG] 정규화 후 빈 제목으로 스킵: '{title}' -> '{normalized_title}'")
                    continue
                
                toc_entry = {
                    "toc_id": str(uuid.uuid4()),
                    "level": level,
                    "title": normalized_title,
                    "page": page,
                    "book_name": Path(pdf_path).stem,
                    "safe_title": self._safe_name(normalized_title)
                }
                results.append(toc_entry)
                print(f"[DEBUG] TOC 항목 추가: {toc_entry}")
            
            print(f"[DEBUG] 최종 TOC 결과: {len(results)}개 항목")
            return results
            
        except Exception as e:
            print(f"[ERROR] TOC 추출 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _is_blacklisted_title(self, raw_title: str) -> bool:
        """블랙리스트 제목 확인"""
        t = self._norm_title(raw_title)
        t = self.NORMALIZE_MAP.get(t, t)
        return t in self.BLACK_TITLES
    
    def _norm_title(self, s: str) -> str:
        """제목 정규화"""
        s = self._nfkc(s).strip()
        
        # PART n / 제n장 / 앞번호 제거
        s = re.sub(r"^\s*(PART|Part)\s*\d+\s*[:.\-]?\s*", "", s)
        s = re.sub(r"^\s*제\s*\d+\s*장\s*[:.\-]?\s*", "", s)
        s = re.sub(r"^\s*\d+(\.\d+)*\s*[:.\-]?\s*", "", s)
        
        # 불릿 포인트 제거
        s = re.sub(r"^\s*[•·▪▫◦‣⁃]\s*", "", s)
        
        return s.strip()
    
    def _nfkc(self, s: str) -> str:
        """유니코드 정규화"""
        return unicodedata.normalize("NFKC", s or "")
    
    def _safe_name(self, s: str) -> str:
        """안전한 파일명 생성"""
        return self.safe_pattern.sub("_", self._nfkc(s)).strip()
