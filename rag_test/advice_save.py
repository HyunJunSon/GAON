# -*- coding: utf-8 -*-
# advice_save.py

import textwrap
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

# ----- DB Update
def update_feedback(conn, analysis_id: str, feedback_text: str):
    sql = "UPDATE analysis_result SET feedback = %s, updated_at = NOW() WHERE analysis_id = %s"
    with conn.cursor() as cur:
        cur.execute(sql, (feedback_text, analysis_id))
    conn.commit()

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

    # ---------------- LLM 프롬프트 작성 + 호출 ----------------
    # 컨텍스트 블록 만들기
    ctx_blocks = []
    for i, s in enumerate(sections, 1):
        txt = s["text"]  # 섹션 전체 본문 그대로 사용
        cite = "; ".join(s["citations"]) or "(no explicit page)"
        ctx_blocks.append(f"[Context {i}] {s['canonical_path']}\n{txt}\n(출처: {cite})")
    ctx_str = "\n\n".join(ctx_blocks)

    system = "You are a kind, concise, and practical Korean communication coach. Ground advice in the provided contexts."
    user = f"""
    최근 대화 분석 요약:
    \"\"\"{summary}\"\"\"

    아래 참고 문맥을 바탕으로 지금 사용자가 당장 쓸 수 있는 조언을 작성해줘.

    {ctx_str}

    지침:
    1) 먼저 2~3문장 핵심 조언.
    2) 이어서 3~6개의 실행 스텝(표현 예시 포함).
    3) 주의할 점 2~3가지.
    4) 3줄 체크리스트.
    5) 끝에 참고 문맥 출처를 불릿 목록으로.
    
    📌 추가 규칙:
    - 각 실행 스텝에는 컨텍스트의 직접 인용(짧은 문장 10~20자)을 포함하고, 따옴표(" ")로 표시할 것.
    - 각 조언 스텝 끝에 (from: Context n) 형식으로 출처 매핑을 명시할 것.
    - 행동 스텝에는 구체적인 수치나 빈도(예: 하루 1회, 5분간, 3회 반복 등)를 포함할 것.

    """.strip()

    print("\n=== ANSWER ===\n")
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.35,
        messages=[
            {"role":"system","content":system},
            {"role":"user","content":user},
        ],
    )
    advice_text = (resp.choices[0].message.content or "").strip()
    print(advice_text)

    # --- 여기서 feedback 컬럼 업데이트 ---
    try:
        with psycopg2.connect(PG_DSN) as conn3:
            update_feedback(conn3, analysis_id, advice_text)
        print("\n[OK] feedback 저장 완료 → analysis_result.feedback 업데이트됨")
    except Exception as e:
        print(f"\n[경고] feedback 저장 중 오류: {e}")

    # 출처만 따로 정리 (중복 제거)
    print("\n--- Sources ---")
    seen = set()
    for s in sections:
        for c in s["citations"]:
            key = (s["canonical_path"], c)
            if key in seen: 
                continue
            seen.add(key)
            print(f"- {key[0]} — {key[1] or '(no explicit page)'}")

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
