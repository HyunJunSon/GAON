-- =========================================
-- ✅ Agent 파이프라인용 DB Migration
-- =========================================
-- 목적: conversation 테이블을 목표 구조로 수정
-- 파일: backend/migration_agent.sql
-- 실행: psql -U your_user -d your_db -f migration_agent.sql
-- =========================================

BEGIN;

-- =========================================
-- 1️⃣ conversation 테이블 수정
-- =========================================

-- ✅ 1-1. 새 컬럼 추가
ALTER TABLE conversation 
ADD COLUMN IF NOT EXISTS conv_id UUID DEFAULT gen_random_uuid() UNIQUE,
ADD COLUMN IF NOT EXISTS conv_start TIMESTAMP,
ADD COLUMN IF NOT EXISTS conv_end TIMESTAMP,
ADD COLUMN IF NOT EXISTS conv_file_id INTEGER REFERENCES conversation_file(id),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- ✅ 1-2. 기존 컬럼명 변경
-- title → cont_title
ALTER TABLE conversation 
RENAME COLUMN title TO cont_title;

-- content → cont_content
ALTER TABLE conversation 
RENAME COLUMN content TO cont_content;

-- create_date → created_at
ALTER TABLE conversation 
RENAME COLUMN create_date TO created_at;

-- ✅ 1-3. conv_id를 NOT NULL로 설정 (기존 데이터에 UUID 자동 생성됨)
UPDATE conversation SET conv_id = gen_random_uuid() WHERE conv_id IS NULL;
ALTER TABLE conversation ALTER COLUMN conv_id SET NOT NULL;

-- ✅ 1-4. updated_at 트리거 생성 (자동 업데이트)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;

$$ LANGUAGE plpgsql;

CREATE TRIGGER update_conversation_updated_at
BEFORE UPDATE ON conversation
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ✅ 1-5. 인덱스 생성 (성능 최적화)
CREATE INDEX IF NOT EXISTS idx_conversation_conv_id ON conversation(conv_id);
CREATE INDEX IF NOT EXISTS idx_conversation_user_id ON conversation(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_family_id ON conversation(family_id);
CREATE INDEX IF NOT EXISTS idx_conversation_created_at ON conversation(created_at);

-- =========================================
-- 2️⃣ analysis_result 테이블 FK 설정
-- =========================================

-- ✅ 2-1. analysis_result.conv_id가 conversation.conv_id를 참조하도록 FK 추가
-- ⚠️ 주의: 기존 데이터가 있으면 실패할 수 있음 (일단 주석 처리)
-- ALTER TABLE analysis_result 
-- ADD CONSTRAINT fk_analysis_result_conv_id 
-- FOREIGN KEY (conv_id) REFERENCES conversation(conv_id) ON DELETE CASCADE;

-- ✅ 2-2. 인덱스 추가 (이미 있을 수 있음)
CREATE INDEX IF NOT EXISTS idx_analysis_result_conv_id ON analysis_result(conv_id);
CREATE INDEX IF NOT EXISTS idx_analysis_result_user_id ON analysis_result(user_id);

COMMIT;

-- =========================================
-- ✅ 3️⃣ 확인 쿼리
-- =========================================

-- conversation 테이블 구조 확인
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'conversation' 
ORDER BY ordinal_position;

-- analysis_result 테이블 구조 확인
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'analysis_result' 
ORDER BY ordinal_position;