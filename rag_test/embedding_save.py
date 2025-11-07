# -*- coding: utf-8 -*-
"""
embedding.py
- chunking_out/chunking_all.jsonl 을 읽어 embed_text(없으면 경로+본문 구성)로 임베딩 생성
- 출력:
  1) --out-jsonl 지정 시: 임베딩 포함 JSONL 라인으로 저장 (embedding: List[float])
  2) --pg-dsn 지정 시: pgvector 테이블에 바로 upsert (테이블 없으면 생성 옵션 제공)

사용 예)
  OpenAI:
    setx OPENAI_API_KEY sk-***
    python embedding.py --in chunking_out/chunking_all.jsonl --out-jsonl embeddings_out.jsonl --provider openai --model text-embedding-3-small --batch-size 64
  로컬(HF):
    pip install sentence-transformers torch --upgrade
    python embedding.py --in chunking_out/chunking_all.jsonl --out-jsonl embeddings_out.jsonl --provider hf --model sentence-transformers/all-MiniLM-L6-v2

  Postgres(pgvector로 바로 적재):
    python embedding.py --in chunking_out/chunking_all.jsonl --provider openai --model text-embedding-3-small --pg-dsn "host=localhost port=5432 dbname=gaon user=gaon_admin password=***" --create-table-if-missing
"""

import os, sys, json, argparse, time
from typing import List, Dict, Iterable, Tuple, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

# ---------- CLI ----------
def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="in_path", default="chunking_out/chunking_all.jsonl", help="chunking_all.jsonl 경로 (기본: chunking_out/chunking_all.jsonl)")
    p.add_argument("--provider", choices=["openai", "hf"], default="openai")
    p.add_argument("--model", default="text-embedding-3-small")
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--sleep", type=float, default=0.0, help="배치 사이 대기(s)")
    p.add_argument("--out-jsonl", default=None, help="임베딩 포함 JSONL 출력 경로")
    p.add_argument("--pg-dsn", default=None, help="host=localhost port=5432 dbname=testdb user=postgres password=1234")
    p.add_argument("--table", default="ref_handbook_snippet", help="pg 테이블명")
    p.add_argument("--create-table-if-missing", action="store_true")
    return p.parse_args()

# ---------- 입출력 ----------
def read_jsonl(path: str) -> Iterable[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

def write_jsonl(path: str, objs: Iterable[Dict]):
    with open(path, "w", encoding="utf-8") as fw:
        for obj in objs:
            fw.write(json.dumps(obj, ensure_ascii=False) + "\n")

# ---------- embed_text 생성 ----------
def build_embed_text(rec: Dict) -> str:
    t = rec.get("embed_text")
    if t:
        return t.strip()
    # fallback: [L1 > L2 > L3] + full_text
    l1, l2, l3 = rec.get("l1_title",""), rec.get("l2_title",""), rec.get("l3_title","")
    parts = [x for x in [l1, l2, l3] if x]
    path = " > ".join(parts)
    body = rec.get("full_text") or ""
    if path:
        return f"[{path}] {body}".strip()
    return body.strip()

# ---------- OpenAI 임베딩 ----------
def embed_openai(texts: List[str], model: str) -> List[List[float]]:
    # openai 패키지 v1 계열
    try:
        from openai import OpenAI
        client = OpenAI()
        resp = client.embeddings.create(model=model, input=texts)
        return [d.embedding for d in resp.data]
    except Exception:
        # 구버전 호환 (openai==0.*)
        import openai  # type: ignore
        openai.api_key = os.getenv("OPENAI_API_KEY")
        resp = openai.Embedding.create(model=model, input=texts)
        return [d["embedding"] for d in resp["data"]]

# ---------- HF 임베딩 ----------
_hf_model = None
def embed_hf(texts: List[str], model_name: str) -> List[List[float]]:
    global _hf_model
    if _hf_model is None:
        from sentence_transformers import SentenceTransformer
        _hf_model = SentenceTransformer(model_name)
    vecs = _hf_model.encode(texts, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=False)
    return [v.astype(float).tolist() for v in vecs]

# ---------- PG 적재 ----------
def ensure_pg_table(conn, table: str, dim: int):
    with conn.cursor() as cur:
        # pgvector 확장
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        # 테이블 (필요 최소 컬럼만, 네 스키마에 맞게 조정 가능)
        cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table} (
          snippet_id UUID PRIMARY KEY,
          book_id UUID,
          book_title TEXT,
          l1_title TEXT,
          l2_title TEXT,
          l3_title TEXT,
          canonical_path TEXT,
          section_id TEXT,
          chunk_ix INT,
          page_start INT,
          page_end INT,
          citation TEXT,
          full_text TEXT,
          embed_text TEXT,
          embedding vector({dim})
        );
        """)
    conn.commit()

def upsert_pg(conn, table: str, rows: List[Dict]):
    """
    rows: 각 객체에 embedding(list[float]) 포함되어 있어야 함
    """
    import psycopg2.extras as extras
    cols = ["snippet_id","book_id","book_title","l1_title","l2_title","l3_title",
            "canonical_path","section_id","chunk_ix","page_start","page_end",
            "citation","full_text","embed_text","embedding"]
    # vector 입력은 리스트를 Python tuple -> psycopg2가 text로 변환, ::vector 캐스팅
    data = []
    for r in rows:
        emb = r["embedding"]
        data.append((
            r.get("snippet_id"),
            r.get("book_id"),
            r.get("book_title"),
            r.get("l1_title"),
            r.get("l2_title"),
            r.get("l3_title"),
            r.get("canonical_path"),
            r.get("section_id"),
            r.get("chunk_ix"),
            r.get("page_start"),
            r.get("page_end"),
            r.get("citation"),
            r.get("full_text"),
            r.get("embed_text"),
            emb,
        ))

    # 임시 테이블로 COPY 후 upsert하거나, execute_values로 upsert
    with conn.cursor() as cur:
        # upsert
        template = "(" + ",".join(["%s"]*14) + ", %s::vector)"  # 마지막 embedding만 ::vector 캐스팅
        insert_sql = f"""
        INSERT INTO {table} ({", ".join(cols)})
        VALUES %s
        ON CONFLICT (snippet_id) DO UPDATE SET
          book_id = EXCLUDED.book_id,
          book_title = EXCLUDED.book_title,
          l1_title = EXCLUDED.l1_title,
          l2_title = EXCLUDED.l2_title,
          l3_title = EXCLUDED.l3_title,
          canonical_path = EXCLUDED.canonical_path,
          section_id = EXCLUDED.section_id,
          chunk_ix = EXCLUDED.chunk_ix,
          page_start = EXCLUDED.page_start,
          page_end = EXCLUDED.page_end,
          citation = EXCLUDED.citation,
          full_text = EXCLUDED.full_text,
          embed_text = EXCLUDED.embed_text,
          embedding = EXCLUDED.embedding;
        """
        extras.execute_values(cur, insert_sql, data, template=template, page_size=500)
    conn.commit()

# ---------- 배치 파이프 ----------
def batch_iter(it: Iterable[Dict], size: int) -> Iterable[List[Dict]]:
    buf = []
    for obj in it:
        buf.append(obj)
        if len(buf) >= size:
            yield buf
            buf = []
    if buf:
        yield buf

def main():
    args = parse_args()

    if not args.pg_dsn:
        args.pg_dsn = os.getenv("PG_DSN")
    
    if not args.out_jsonl and not args.pg_dsn:
        Path("embedding_out").mkdir(parents=True, exist_ok=True)
        args.out_jsonl = "embedding_out/embeddings_all.jsonl"

    # provider 준비
    provider = args.provider
    model = args.model
    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY 환경변수가 필요합니다.", file=sys.stderr)
        sys.exit(2)

    # PG 연결(선택)
    conn = None
    dim_hint = None
    if provider == "openai":
        # 대표 모델 차원 힌트 (필요 시 추가)
        dim_hint = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
        }.get(model, 1536)
    else:
        # HF 모델별 차원은 로드 후 알 수 있지만, 대개 알려져 있음
        dim_hint = 384 if "MiniLM-L6" in model else 768

    if args.pg_dsn:
        import psycopg2
        conn = psycopg2.connect(args.pg_dsn)
        if args.create_table_if_missing:
            ensure_pg_table(conn, args.table, dim_hint)

    # 출력 JSONL 스트림 준비(선택)
    writer = None
    out_objs = []
    if args.out_jsonl:
        # 즉시쓰기 대신 순서 보존 위해 버퍼링 or 라인 단위 즉시쓰기 중 택1
        # 여기서는 즉시쓰기
        writer = open(args.out_jsonl, "w", encoding="utf-8")

    total, done = 0, 0
    t0 = time.time()

    def do_write(objs: List[Dict]):
        nonlocal writer, conn, args
        if writer:
            for o in objs:
                writer.write(json.dumps(o, ensure_ascii=False) + "\n")
        if conn:
            upsert_pg(conn, args.table, objs)

    # 배치 처리
    for batch in batch_iter(read_jsonl(args.in_path), args.batch_size):
        texts = []
        for r in batch:
            et = build_embed_text(r)
            r["embed_text"] = et
            texts.append(et)

        # 임베딩
        if provider == "openai":
            vecs = embed_openai(texts, model)
        else:
            vecs = embed_hf(texts, model)

        # 결과 합치기
        out_batch = []
        for r, v in zip(batch, vecs):
            r["embedding"] = v
            out_batch.append(r)

        do_write(out_batch)
        done += len(out_batch)
        if args.sleep > 0:
            time.sleep(args.sleep)

        # 간단 로그
        if done % (args.batch_size * 10) == 0:
            elapsed = time.time() - t0
            print(f"[embed] {done} rows, {elapsed:.1f}s")

    if writer:
        writer.close()
    if conn:
        conn.close()

    print("✅ done.")

if __name__ == "__main__":
    main()
