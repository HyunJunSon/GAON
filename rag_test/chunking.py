# -*- coding: utf-8 -*-
"""
chunking.py
- 가장 작은 목차(leaf) 단위로 PDF 텍스트를 추출하여 600~800자로 청킹
- 입력:  toc_out/book_toc_*.jsonl, pdf변환_downloads/*.pdf
- 출력:  chunking_out/snippets_{book}.jsonl, chunking_out/chunking_all.jsonl
"""
import json
import uuid
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Tuple
import fitz  # pip install pymupdf

# -------------------- 경로/파라미터 --------------------
ROOT     = Path(__file__).resolve().parents[0]
PDF_DIR  = ROOT / "pdf변환_downloads"
TOC_DIR  = ROOT / "toc_out"
OUT_DIR  = ROOT / "chunking_out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ALL_OUT_JSON = OUT_DIR / "chunking_all.jsonl"

MIN_CHARS, MAX_CHARS = 600, 800   # 요구사항: 600~800자
SAVE_FULL_TEXT = True             # 본문 저장

# -------------------- 유틸 --------------------
def safe_name(s: str) -> str:
    return re.sub(r'[\\/:*?"<>|]+', "_", s or "").strip()

def norm_text(s: str, max_len: int | None = None) -> str:
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    if max_len:
        s = s[:max_len]
    return s

def load_toc_lines(path: Path) -> List[Dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows

def build_parent_index(rows: List[Dict]) -> Tuple[Dict[str, Dict], Dict[str, List[Dict]]]:
    """toc_id -> row, parent_toc_id -> [children] 인덱스 생성"""
    by_id = {r["toc_id"]: r for r in rows}
    children: Dict[str, List[Dict]] = {}
    for r in rows:
        pid = r.get("parent_toc_id")
        if pid:
            children.setdefault(pid, []).append(r)
    return by_id, children

def is_leaf(row: Dict, children_index: Dict[str, List[Dict]]) -> bool:
    """가장 작은 목차(leaf) 판정: blacklisted 아니고 children 없음, level>=2"""
    if row.get("is_blacklisted", False):
        return False
    if int(row.get("level", 0)) < 2:
        return False
    return row["toc_id"] not in children_index

def collect_path_titles(row: Dict, by_id: Dict[str, Dict]) -> List[str]:
    """현재 row 기준으로 level 1까지 parent를 타고 올라가 제목 경로 생성(위->아래 정렬)"""
    path = []
    cur = row
    # 안전 루프
    for _ in range(12):
        title = norm_text(cur.get("norm_title") or cur.get("title"))
        level = int(cur.get("level", 0))
        path.append((level, title))
        pid = cur.get("parent_toc_id")
        if not pid or pid not in by_id:
            break
        cur = by_id[pid]
    # level 오름차순 정렬 후 제목만 추출
    path = [t for _, t in sorted(path, key=lambda x: x[0])]
    return path  # [L1, L2, L3, ...현재]

def pad_path_to_3(path: List[str]) -> Tuple[str, str, str]:
    """경로를 L1/L2/L3 3칸으로 패딩 (없으면 빈문자)"""
    l1 = path[0] if len(path) > 0 else ""
    l2 = path[1] if len(path) > 1 else ""
    l3 = path[2] if len(path) > 2 else ""
    return l1, l2, l3

def extract_text_by_pages(pdf_path: Path, s: int, e: int) -> str:
    """PDF 페이지 범위(1-based, inclusive) 텍스트 추출"""
    with fitz.open(str(pdf_path)) as doc:
        s = max(1, int(s)); e = max(s, int(e))
        last = doc.page_count
        if e > last:
            e = last
        parts = []
        for pg in range(s - 1, e):
            parts.append(doc.load_page(pg).get_text("text") or "")
    return "\n".join(parts)

# -------------------- 청킹 (문단/문장 경계 우선, 600~800자) --------------------
# 고정 길이 lookbehind만 사용 (파이썬 re 제약)
_SENT_SPLIT = re.compile(r'(?:(?<=[\.!\?。！？][\'"\)\]])|(?<=[\.!\?。！？]))\s+(?=[^\s])')

def split_paragraphs(text: str) -> List[str]:
    """
    빈 줄 기준 문단 분리. [KEY POINT]는 문단 경계로 잘리고 앞에서 새 문단 시작되도록 처리.
    """
    # [KEY POINT] 앞에서 끊기 쉽게 개행 삽입
    text = re.sub(r"\s*\[KEY POINT\]\s*", "\n[KEY POINT] ", text)
    t = text.replace("\r", "")
    blocks, cur = [], []
    for line in t.split("\n"):
        if line.strip():
            cur.append(line.strip())
        else:
            if cur:
                blocks.append(" ".join(cur).strip())
                cur = []
    if cur:
        blocks.append(" ".join(cur).strip())
    return [b for b in blocks if b]

def chunk_text_600_800(txt: str, min_len=MIN_CHARS, max_len=MAX_CHARS) -> List[str]:
    """
    규칙:
      - 문단 우선으로 누적하되, '문단 하나가 max_len을 넘으면' 반드시 문장 단위로 분해
      - 문장들을 그리디로 묶어서 [min_len, max_len] 범위 맞춤
      - 어떤 경우에도 max_len 초과 조각이 남지 않도록 마지막에 하드컷 세이프가드
    """
    chunks: List[str] = []
    buf = ""

    def flush():
        nonlocal buf
        if buf.strip():
            chunks.append(buf.strip())
            buf = ""

    def pack_sentences(sentences: List[str]):
        """문장 리스트를 그리디로 [min,max] 범위로 포장하여 chunks에 추가"""
        nonlocal buf
        cur = buf.strip()
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
            cand = (cur + (" " if cur else "") + sent).strip()
            if len(cand) <= max_len:
                cur = cand
            else:
                # 현재 포장이 min 이상이면 내보내고 새 포장 시작
                if len(cur) >= min_len:
                    chunks.append(cur)
                    cur = sent
                    # 새 문장 하나가 너무 길면(개별 문장 자체가 max 초과) 하드컷
                    while len(cur) > max_len:
                        chunks.append(cur[:max_len].strip())
                        cur = cur[max_len:].strip()
                else:
                    # min 미만인데 붙이면 max 초과 → 현재 cur를 방출하고 sent로 시작
                    if cur:
                        chunks.append(cur)
                    cur = sent
                    while len(cur) > max_len:
                        chunks.append(cur[:max_len].strip())
                        cur = cur[max_len:].strip()
        # 남은 포장은 buf로 돌려 다음 문단과 이어 붙임
        buf = cur

    for para in split_paragraphs(txt):
        para = para.strip()
        if not para:
            continue

        # 1) 문단이 짧아서 통째로 붙여도 되면 버퍼에 그리디로 누적
        cand = (buf + ("\n\n" if buf else "") + para).strip()
        if len(para) <= max_len and len(cand) <= max_len:
            buf = cand
            continue

        # 2) 여기로 왔다는 건 (a) 문단 단독으로도 길거나, (b) 버퍼와 합치면 초과
        #    문단이 max를 넘기면 '항상' 문장 분해해서 포장
        if len(para) > max_len:
            sentences = _SENT_SPLIT.split(para)
            pack_sentences(sentences)
            # 세이프가드
            if len(buf) > max_len:
                while len(buf) > max_len:
                    chunks.append(buf[:max_len].strip())
                    buf = buf[max_len:].strip()
            continue

        # 3) 문단은 짧지만 버퍼와 합치면 초과하는 경우
        #    버퍼가 min 이상이면 먼저 비우고, 그 다음 새 문단을 시작
        if len(buf) >= min_len:
            flush()
            # 새 문단 시작
            if len(para) <= max_len:
                buf = para
            else:
                sentences = _SENT_SPLIT.split(para)
                pack_sentences(sentences)
        else:
            # buf가 너무 짧을 때는 문장 분해로 두 조각을 자연스럽게 맞춘다
            # (buf + para)를 문장 단위로 다시 포장
            combined = (buf + (" " if buf else "") + para).strip()
            sentences = _SENT_SPLIT.split(combined)
            buf = ""  # 재포장을 위해 초기화
            pack_sentences(sentences)

    # 마지막 남은 버퍼 처리
    if buf:
        if len(buf) > max_len:
            while len(buf) > max_len:
                chunks.append(buf[:max_len].strip())
                buf = buf[max_len:].strip()
        if buf:
            # 너무 짧으면 직전 조각과 병합 시도
            if chunks and len(buf) < (min_len // 2) and len(chunks[-1]) + 2 + len(buf) <= max_len:
                chunks[-1] = (chunks[-1] + "\n\n" + buf).strip()
            else:
                chunks.append(buf.strip())

    # 최종 트리밍 + 세이프가드 (절대 max 초과 금지)
    out = []
    for c in chunks:
        c = c.strip()
        if not c:
            continue
        if len(c) <= max_len:
            out.append(c)
        else:
            # 혹시 모를 초과는 하드컷
            start = 0
            while start < len(c):
                out.append(c[start:start + max_len].strip())
                start += max_len
    return out

# -------------------- 사후 보정(절대 800자 초과 금지 + 자연스러운 경계 우선) --------------------
def _smart_split_once(s: str, max_len: int) -> List[str]:
    """
    s가 max_len을 넘으면 가장 자연스러운 경계에서 두 조각 이상으로 자른다.
    우선순위: [KEY POINT] / 번호·불릿 / 문장부호 / 공백 / 최후수단 하드컷
    재귀적으로 호출된다.
    """
    s = s.strip()
    if len(s) <= max_len:
        return [s] if s else []

    # 1) [KEY POINT] 앞에서 자르기 (가능한 가장 오른쪽 경계)
    idx = s.rfind("[KEY POINT]", 0, max_len)
    if idx > 0:
        left = s[:idx].rstrip()
        right = s[idx:].lstrip()
        return ([left] if left else []) + _smart_split_once(right, max_len)

    # 2) 번호/불릿 경계
    for pat in [r"\n+\s*\d+\s", r"\s\d+\s", r"\s•\s", r"\s-\s"]:
        m = list(re.finditer(pat, s))
        cut = max([mm.start() for mm in m if mm.start() < max_len], default=-1)
        if cut > 0:
            left = s[:cut].rstrip()
            right = s[cut:].lstrip()
            return ([left] if left else []) + _smart_split_once(right, max_len)

    # 3) 문장부호(가장 오른쪽)에서 자르기
    punct = max(s.rfind(p, 0, max_len) for p in [".", "!", "?", "。", "！", "？"])
    if punct > 0:
        left = s[:punct+1].rstrip()
        right = s[punct+1:].lstrip()
        return ([left] if left else []) + _smart_split_once(right, max_len)

    # 4) 공백에서 자르기
    space = s.rfind(" ", 0, max_len)
    if space > 0:
        left = s[:space].rstrip()
        right = s[space+1:].lstrip()
        return ([left] if left else []) + _smart_split_once(right, max_len)

    # 5) 최후수단: 하드컷
    left = s[:max_len].rstrip()
    right = s[max_len:].lstrip()
    return ([left] if left else []) + _smart_split_once(right, max_len)

def enforce_length(chunks: List[str], min_len: int, max_len: int) -> List[str]:
    """
    - 모든 조각이 max_len 초과하지 않도록 강제 분할
    - 마지막 꼬리 조각이 너무 짧으면 직전과 병합(가능하면)
    """
    fixed: List[str] = []
    for c in chunks:
        parts = _smart_split_once(c.strip(), max_len)
        fixed.extend(p for p in parts if p.strip())

    # 마지막 꼬리 병합 시도
    if len(fixed) >= 2 and len(fixed[-1]) < (min_len // 2):
        tail = fixed.pop()
        if len(fixed[-1]) + 2 + len(tail) <= max_len:
            fixed[-1] = (fixed[-1] + "\n\n" + tail).strip()
        else:
            fixed.append(tail)
    return fixed

# -------------------- 메인 로직 --------------------
def process_one_book(toc_jsonl_path: Path, all_fw) -> int:
    rows = load_toc_lines(toc_jsonl_path)
    if not rows:
        return 0

    by_id, children_index = build_parent_index(rows)
    pdf_names = sorted({r["source_file"] for r in rows})
    book_title = rows[0].get("book_title") or Path(pdf_names[0]).stem
    book_title = norm_text(book_title)
    out_path = OUT_DIR / f"snippets_{safe_name(book_title)}.jsonl"

    total_written = 0
    with out_path.open("w", encoding="utf-8") as fw:
        for pdf_name in pdf_names:
            pdf_path = PDF_DIR / pdf_name
            if not pdf_path.exists():
                continue

            # leaf 섹션만 타깃
            targets = [r for r in rows if r.get("source_file") == pdf_name and is_leaf(r, children_index)]
            # 문서상 순서 보장
            targets.sort(key=lambda x: int(x.get("order_ix", 0)))

            for leaf in targets:
                s, e = int(leaf["page_start"]), int(leaf["page_end"])
                raw_text = extract_text_by_pages(pdf_path, s, e)
                raw_text = norm_text(raw_text)
                if not raw_text:
                    continue

                # 경로/제목
                path_titles = collect_path_titles(leaf, by_id)  # [L1, L2, L3, ..., leaf]
                l1, l2, l3 = pad_path_to_3(path_titles[:3])
                display_path = " > ".join([t for t in [l1, l2, l3] if t])

                # 본문 청킹 (600~800자)
                chunks = chunk_text_600_800(raw_text, MIN_CHARS, MAX_CHARS)
                # 사후 보정으로 절대 800 초과 금지 + 꼬리 병합
                chunks = enforce_length(chunks, MIN_CHARS, MAX_CHARS)
                if not chunks:
                    continue

                # 메타
                book_id   = leaf.get("book_id")
                toc_id    = leaf.get("toc_id")
                citation  = norm_text(f"{(leaf.get('norm_title') or leaf.get('title') or '').strip()} p.{s}-{e}", 400)

                for ix, ck in enumerate(chunks):
                    rec = {
                        "snippet_id": str(uuid.uuid4()),
                        "book_id": book_id,
                        "book_title": book_title,
                        "l1_title": l1,
                        "l2_title": l2,
                        "l3_title": l3,
                        "canonical_path": display_path,
                        "section_id": toc_id,       # leaf 단위
                        "chunk_ix": ix,             # 0-based
                        "page_start": s,
                        "page_end": e,
                        "citation": citation,
                        "full_text": ck if SAVE_FULL_TEXT else None,
                        # 나중 임베딩 시 그대로 쓰면 됨
                        "embed_text": f"[{display_path}] {ck}",
                        "embedding": None
                    }
                    line = json.dumps(rec, ensure_ascii=False)
                    fw.write(line + "\n")
                    all_fw.write(line + "\n")
                    total_written += 1

    print(f"✅ {book_title} 청킹 저장: {out_path} ({total_written} rows)")
    return total_written

def run():
    toc_files = sorted(TOC_DIR.glob("book_toc_*.jsonl"))
    if not toc_files:
        raise FileNotFoundError(f"TOC 파일이 없습니다: {TOC_DIR}")

    grand_total = 0
    with ALL_OUT_JSON.open("w", encoding="utf-8") as all_fw:
        for toc_jsonl in toc_files:
            grand_total += process_one_book(toc_jsonl, all_fw)

    print(f"\n📦 합본 저장: {ALL_OUT_JSON} (총 {grand_total} rows)")

if __name__ == "__main__":
    run()
