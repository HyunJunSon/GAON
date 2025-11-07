# rag_test
bucket -> toc_extract -> chunking -> embedding_save

bucket.py 실행시 pdf변환_downloads폴더가 생기면서 gcp에있는 pdf파일 다운됨\
toc_extract.py 실행시 다운받은 pdf파일의 toc(목차카탈로그)를 추출해서 toc_out 폴더의 json파일로 저장 (대분류, 중분류, 소분류, 페이지 번호 저장됨)\
chunking.py 실행시 가장 작은 목차 분류를 기준으로 600~800자 청킹-> 임베드 텍스트(대,중,소 제목 + 본문청크)저장 (toc_out폴더의 json파일을 참고해서 pdf변환_downloads폴더의 pdf파일을 청킹함)\
embedding_save.py 실행시 임베드 텍스트를 벡터화하고 전체 jsonl을 postgresql에 저장함\
$ python embedding_save.py --create-table-if-missing\

embedding_data_analysis -> \
embedding_data_analysis.py data_analysis의 summary부분만 벡터화 시켜도 될듯함\

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
