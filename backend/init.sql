-- pgvector 확장을 활성화 (한 번만 실행)
CREATE EXTENSION IF NOT EXISTS vector;

-- user 테이블 생성
CREATE TABLE user (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    create_date TIMESTAMP NOT NULL
);

-- family 테이블 생성
CREATE TABLE family (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    create_date TIMESTAMP NOT NULL
);

-- conversation 테이블 생성
CREATE TABLE conversation (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    user_id INTEGER REFERENCES user(id),
    family_id INTEGER REFERENCES family(id),
    create_date TIMESTAMP NOT NULL
);

-- ideal_answer 테이블 생성 (RAG 시스템용)
CREATE TABLE ideal_answer (
    idea_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),              -- 모범답안ID
    source TEXT,                                                     -- 원문
    embedding VECTOR(1536),                                          -- 임베딩 (pgvector)
    created_at TIMESTAMP DEFAULT NOW(),                              -- 생성일
    analysisid UUID                                                  -- 분석결과ID (외래키 가능)
);

-- created_at 컬럼에 인덱스 생성 (성능 최적화)
CREATE INDEX idx_ideal_answer_created_at ON ideal_answer(created_at);

-- source 컬럼에 GIN 인덱스 생성 (全文 검색용)
CREATE INDEX idx_ideal_answer_source ON ideal_answer USING gin(to_tsvector('english', source));

-- embedding 컬럼에 ivfflat 인덱스 생성 (벡터 유사도 검색 최적화)
CREATE INDEX idx_ideal_answer_embedding ON ideal_answer USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

