-- FK 제약 조건 제거
ALTER TABLE conversation DROP CONSTRAINT IF EXISTS fk_conversation_file;