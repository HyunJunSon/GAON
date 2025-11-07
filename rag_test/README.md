# rag_test
bucket -> toc_extract -> chunking -> embedding_save

bucket.py 실행시 pdf변환_downloads폴더가 생기면서 gcp에있는 pdf파일 다운됨\
toc_extract.py 실행시 다운받은 pdf파일의 toc(목차카탈로그)를 추출해서 toc_out 폴더의 json파일로 저장 (대분류, 중분류, 소분류, 페이지 번호 저장됨)\
chunking.py 실행시 가장 작은 목차 분류를 기준으로 600~800자 청킹-> 임베드 텍스트(대,중,소 제목 + 본문청크)저장 (toc_out폴더의 json파일을 참고해서 pdf변환_downloads폴더의 pdf파일을 청킹함)\
embedding_save.py 실행시 임베드 텍스트를 벡터화하고 전체 jsonl을 postgresql에 저장함\
$ python embedding_save.py --create-table-if-missing\

summary_rag.py -> \
summary_rag.py 실행시 data_analysis의 analysis_id 최신에 따른 summary부분만 벡터화 시켜서 ref_handbook_snippet 책의 pgvector KNN 검색 후 같은 section_id는 chunk_ix 순으로 자동 스티칭 후 상위 섹션들 프리뷰(본문 앞부분 + citation) 출력
(검색 결과 미리보기단계)
http://dev.wyhil.com:43000/SG-OHA-2025-TEAM-04/GAON/raw/branch/feature/%235/rag_test/20251107_171549.png

retriever.py 실행시 data_analysis의 interest, tone, top_words, summary를 고려하여 책 가져옴\
텍스트 인덱스(FTS, trigram)\
CREATE INDEX IF NOT EXISTS idx_snip_fts ON ref_handbook_snippet USING GIN (to_tsvector('simple', embed_text)); \
CREATE INDEX IF NOT EXISTS idx_snip_trgm ON ref_handbook_snippet USING GIN (embed_text gin_trgm_ops); \
벡터 인덱스(pgvector)\

(청킹은 임베딩 효율 때문에 필수 (짧을수록 의미 명확)
문맥 손실은 post-processing에서 재조립으로 해결
즉, “짤리는 건 저장용 기술적 분리일 뿐”, 최종 출력은 “자연스럽게 연결된 문단”)\



<pre>gcloud auth application-default login
pip install google-cloud-storage
pip install pymupdf
</pre>
