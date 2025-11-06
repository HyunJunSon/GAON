# -*- coding: utf-8 -*-
import json, uuid, re, unicodedata
from pathlib import Path
import fitz  # pip install pymupdf

ROOT     = Path(__file__).resolve().parent
PDF_DIR  = ROOT / "pdf변환_downloads"
OUT_DIR  = ROOT / "toc_out"
OUT_DIR.mkdir(parents=True, exist_ok=True)
ALL_JSON = OUT_DIR / "book_toc_all.jsonl"

SAFE = re.compile(r'[\\/:*?"<>|]+')

# 📌 블랙리스트 강화: 프롤로그/머리말/처음으로/추천사도 제외
# 📌 정확 일치 블랙리스트 (오탐 방지용)
BLACK_TITLES = {
    "차례", "목차", "판권", "표지",
    "프롤로그", "머리말", "추천사",
    "저자 소개", "여는 말",
    "책의 시작", "처음으로",
}

# 붙여쓰기 등 자주 나오는 변형 교정
NORMALIZE_MAP = {
    "저자소개": "저자 소개",
    "여는말": "여는 말",
}

def is_blacklisted_title(raw_title: str) -> bool:
    # 번호/불릿 제거 포함한 너의 norm_title 이용
    t = norm_title(raw_title)
    # 붙여쓰기 보정
    t = NORMALIZE_MAP.get(t, t)
    # 정확 일치로만 블랙 처리
    return t in BLACK_TITLES


def nfkc(s: str) -> str:
    return unicodedata.normalize("NFKC", s or "")

def safe_name(s: str) -> str:
    return SAFE.sub("_", nfkc(s)).strip()

def norm_title(s: str) -> str:
    s = nfkc(s).strip()

    # PART n / 제n장 / 앞번호 01. 1.1. 등 제거
    s = re.sub(r"^\s*(PART|Part)\s*\d+\s*[:.\-]?\s*", "", s)
    s = re.sub(r"^\s*제\s*\d+\s*장\s*[:.\-]?\s*", "", s)
    s = re.sub(r"^\s*\d+(\.\d+)*\s*[:.\-]?\s*", "", s)

    # 선행 불릿류(여러 유니코드) 제거
    s = re.sub(r"^[\u00B7\u2022\u2027\u2219\-\–\—\.\s]+", "", s)

    # 중복 공백 정리
    s = re.sub(r"\s+", " ", s).strip()
    return s

def compute_ranges(toc, last_page: int):
    out = []
    for i, (lvl, title, p) in enumerate(toc):
        # PyMuPDF TOC 값 정규화
        lvl = int(lvl)
        title = nfkc(title).strip()
        s = max(1, int(p))
        e = int(toc[i + 1][2] - 1) if i + 1 < len(toc) else int(last_page)

        # 페이지 보정
        if e < s:
            # 다음 북마크가 역전일 때 0폭으로 보정
            e = s
        if e > last_page:
            e = last_page

        out.append((lvl, title, s, e))
    return out

def make_book_id(title: str) -> str:
    NAMESPACE = uuid.UUID("11111111-1111-1111-1111-111111111111")
    key = re.sub(r"\s+", " ", nfkc(title).strip().lower())
    return str(uuid.uuid5(NAMESPACE, key))

def make_toc_id(book_id: str, title: str, page_start: int) -> str:
    NAMESPACE = uuid.UUID("00000000-0000-0000-0000-000000000000")
    return str(uuid.uuid5(NAMESPACE, f"{book_id}|{nfkc(title)}|{int(page_start)}"))

def run():
    pdfs = sorted(list(PDF_DIR.glob("*.pdf")) + list(PDF_DIR.glob("*.PDF")))
    if not pdfs:
        raise FileNotFoundError(f"❌ PDF 파일이 없습니다: {PDF_DIR}")

    # 합본 중복 방지 세트(세션 내)
    seen_all = set()  # (book_id, toc_id)

    with open(ALL_JSON, "w", encoding="utf-8") as fall:
        for pdf in pdfs:
            book_name = pdf.stem
            book_id   = make_book_id(book_name)
            out_json  = OUT_DIR / f"book_toc_{safe_name(book_name)}.jsonl"

            print(f"\n📘 {book_name} 처리 중...")

            try:
                doc = fitz.open(str(pdf))
                toc = doc.get_toc(simple=True)
                if not toc:
                    print(f"[WARN] TOC 없음: {pdf.name}")
                    continue

                ranges = compute_ranges(toc, doc.page_count)
                stack  = []  # [(level, toc_id)]
                order  = 0

                seen_book = set()  # (lvl, title, page_start) 중복 방지

                with open(out_json, "w", encoding="utf-8") as fw:
                    for lvl, title, s, e in ranges:
                        key_local = (lvl, title, s)
                        if key_local in seen_book:
                            # 같은 항목이 여러 번 찍히는 경우 스킵
                            continue
                        seen_book.add(key_local)

                        order += 1
                        t_norm  = norm_title(title)
                        toc_id  = make_toc_id(book_id, title, s)

                        # 부모 연결(루트 보호)
                        while stack and int(stack[-1][0]) >= int(lvl):
                            stack.pop()
                        parent_id = stack[-1][1] if stack else None
                        stack.append((int(lvl), toc_id))

                        rec = {
                            "book_id": book_id,
                            "book_title": nfkc(book_name),
                            "toc_id": toc_id,
                            "level": int(lvl),
                            "title": nfkc(title),
                            "norm_title": t_norm,
                            "parent_toc_id": parent_id,
                            "page_start": int(s),
                            "page_end": int(e),
                            "order_ix": int(order),
                            "source_file": pdf.name,
                            "is_blacklisted": is_blacklisted_title(title),
                        }

                        # 합본 중복 방지
                        k = (book_id, toc_id)
                        if k not in seen_all:
                            seen_all.add(k)
                            fall.write(json.dumps(rec, ensure_ascii=False) + "\n")

                        fw.write(json.dumps(rec, ensure_ascii=False) + "\n")

                print(f"✅ 저장 완료: {out_json}")

            except Exception as ex:
                print(f"[ERROR] {pdf.name}: {ex}")
            finally:
                try:
                    doc.close()
                except:
                    pass

    print(f"\n📦 합본 저장: {ALL_JSON}")

if __name__ == "__main__":
    run()
