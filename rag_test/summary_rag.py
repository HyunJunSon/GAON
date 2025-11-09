# -*- coding: utf-8 -*-
# summary_rag.py
# - analysis_id가 주어지면 해당 요약으로, 없으면 created_at 최신 요약으로
# - 요약 임베딩 → pgvector KNN → section 스티칭 → 프리뷰

import os, sys, json
import psycopg2
import psycopg2.extras as extras
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# ----- .env 로딩 (현재 폴더/상위 폴더 우선 탐색) -----
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

# ----- DB helpers -----
def fetch_analysis_by_id(conn, analysis_id: str) -> dict:
    sql = "SELECT * FROM analysis_result WHERE analysis_id = %s LIMIT 1"
    with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
        cur.execute(sql, (analysis_id,))
        row = cur.fetchone()
    if not row:
        return {}
    for k in ("statistics", "style_analysis"):
        if isinstance(row.get(k), str):
            try: row[k] = json.loads(row[k])
            except: pass
    return row

def fetch_latest_analysis_id_by_created(conn, user_id: str|None=None, conv_id: str|None=None) -> str|None:
    base = "SELECT analysis_id FROM analysis_result"
    where, params = [], []
    if user_id:
        where.append("user_id = %s"); params.append(user_id)
    if conv_id:
        where.append("conv_id = %s"); params.append(conv_id)
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    sql = f"""{base}{where_sql}
              ORDER BY created_at DESC NULLS LAST
              LIMIT 1"""
    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
    return row[0] if row else None

def fetch_full_sections(conn, table: str, section_ids: list[str]) -> list[dict]:
    """
    주어진 section_id 들에 대해, 섹션에 속한 모든 스니펫을 가져와
    chunk_ix / page 순으로 정렬 → 전체 본문/인용을 재조립.
    """
    if not section_ids:
        return []

    sql = f"""
      SELECT section_id, canonical_path, chunk_ix,
             page_start, page_end, citation, full_text
      FROM {table}
      WHERE section_id = ANY(%s)
      ORDER BY section_id, chunk_ix, page_start, page_end
    """
    with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
        cur.execute(sql, (section_ids,))
        rows = cur.fetchall()

    by = {}
    for r in rows:
        g = by.setdefault(r["section_id"], {
            "section_id": r["section_id"],
            "canonical_path": r["canonical_path"],
            "snippets": [],
            "citations": set(),
        })
        g["snippets"].append(r)
        if r.get("citation"):
            g["citations"].add(r["citation"])

    sections = []
    for sec in by.values():
        text = "\n\n".join(x["full_text"] for x in sec["snippets"] if x.get("full_text"))
        sections.append({
            "section_id": sec["section_id"],
            "canonical_path": sec["canonical_path"],
            "text": text.strip(),
            "citations": sorted(sec["citations"]),
        })
    return sections

# ----- Embedding / KNN / Stitch -----
def make_query_embedding(client: OpenAI, text: str, model="text-embedding-3-small") -> list:
    t = (text or "").strip()
    if not t:
        raise ValueError("summary is empty")
    return client.embeddings.create(model=model, input=[t]).data[0].embedding

def knn_search(conn, qvec: list, table: str, limit: int = 50):
    sql = f"""
      SELECT snippet_id, section_id, canonical_path, chunk_ix,
             page_start, page_end, citation, full_text,
             (embedding <#> %s::vector) AS distance
      FROM {table}
      ORDER BY embedding <#> %s::vector
      LIMIT %s
    """
    with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
        cur.execute(sql, (qvec, qvec, limit))
        return cur.fetchall()

def stitch_by_section(rows, top_k=6):
    by = {}
    for r in rows:
        g = by.setdefault(r["section_id"], {
            "canonical_path": r["canonical_path"],
            "snippets": [], "cites": set(), "best": r["distance"]
        })
        g["snippets"].append(r)
        if r.get("citation"):
            g["cites"].add(r["citation"])
        g["best"] = min(g["best"], r["distance"])
    sections = []
    for sid, g in by.items():
        g["snippets"].sort(key=lambda x: (x["chunk_ix"], x["page_start"], x["page_end"]))
        text = "\n\n".join(x["full_text"] for x in g["snippets"] if x.get("full_text"))
        sections.append({
            "section_id": sid,
            "canonical_path": g["canonical_path"],
            "text": text.strip(),
            "citations": sorted(g["cites"]),
            "best_dist": g["best"],
        })
    sections.sort(key=lambda s: s["best_dist"])
    return sections[:top_k]

# ----- Main -----
def main():
    PG_DSN  = os.getenv("PG_DSN")
    API_KEY = os.getenv("OPENAI_API_KEY")
    if not (PG_DSN and API_KEY):
        print("PG_DSN / OPENAI_API_KEY 필요"); sys.exit(1)

    # analysis_id 인자(optional): 없으면 created_at 최신 자동 선택
    analysis_id = sys.argv[1].strip() if len(sys.argv) >= 2 else None
    table = (len(sys.argv) > 2 and sys.argv[2]) or os.getenv("RAG_TABLE") or "ref_handbook_snippet"

    # 최신 자동 선택 시 범위(선택): TEST_USER_ID / TEST_CONV_ID
    default_user_id = os.getenv("TEST_USER_ID") or None
    default_conv_id = os.getenv("TEST_CONV_ID") or None

    client = OpenAI(api_key=API_KEY)

    with psycopg2.connect(PG_DSN) as conn:
        if not analysis_id:
            analysis_id = fetch_latest_analysis_id_by_created(conn, default_user_id, default_conv_id)
            if not analysis_id:
                print("최신 analysis_id 없음"); sys.exit(1)

        row = fetch_analysis_by_id(conn, analysis_id)
        if not row:
            print("analysis_result 레코드 없음"); sys.exit(1)

        summary = (row.get("summary") or "").strip()
        if not summary:
            print("summary 비어있음"); sys.exit(1)

        qvec = make_query_embedding(client, summary)
        rows = knn_search(conn, qvec, table=table, limit=50)

    # ⬇️ 섹션별 최소 distance 맵 (KNN rows에서 계산)
    best_dist_map = {}
    for r in rows:
        sid = r["section_id"]
        d = r.get("distance")
        if d is None:
            continue
        if sid not in best_dist_map or d < best_dist_map[sid]:
            best_dist_map[sid] = d

    # 1) 히트된 section_id 수집
    hit_section_ids = sorted({r["section_id"] for r in rows})

    # 2) 섹션 전체 본문을 DB에서 다시 가져와 재조립 (=> cite도 섹션 전체 기준)
    with psycopg2.connect(PG_DSN) as conn2:
        sections = fetch_full_sections(conn2, table, hit_section_ids)

    # 3) 각 섹션에 KNN에서 계산한 최소 distance를 주입
    for s in sections:
        s["best_dist"] = best_dist_map.get(s["section_id"])

    # 4) distance 기준으로 정렬 후 상위 k개만 선택
    sections.sort(key=lambda z: (float("inf") if z.get("best_dist") is None else z["best_dist"]))
    sections = sections[:6]

    print(f"\n=== ANALYSIS_ID ===\n{analysis_id}")
    print("\n=== SUMMARY (query) ===\n", summary)
    print("\n=== TOP SECTIONS ===")
    if not sections:
        print("(no sections)")

    # 🔹 PREVIEW_LINES = 몇 줄까지 출력할지 
    preview_lines = int(os.getenv("PREVIEW_LINES") or 2)

    for i, s in enumerate(sections, 1):
        lines = s["text"].splitlines()
        body = "\n".join(lines[:preview_lines])
        if len(lines) > preview_lines:
            body += "\n   … (이하 생략)"

        cite = "; ".join(s["citations"]) or "(no explicit page)"
        d = s.get("best_dist")
        d_str = f"{d:.4f}" if isinstance(d, (int, float)) else "-"

        print(f"{i}. {s['canonical_path']}  dist={d_str}\n   {body}\n   cite: {cite}\n")

if __name__ == "__main__":
    main()
