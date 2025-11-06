# rag_test
bucket -> toc_extract -> chunking -> embedding

bucket.py 실행시 pdf변환_downloads폴더가 생기면서 gcp에있는 pdf파일 다운됨\
toc_extract.py 실행시 다운받은 pdf파일의 toc(목차카탈로그)를 추출해서 toc_out 폴더의 json파일로 저장 (대분류, 중분류, 소분류, 페이지 번호 저장됨)\
chunking.py 실행시 가장 작은 목차 분류를 기준으로 600~800자 청킹 (toc_out폴더의 json파일을 참고해서 pdf변환_downloads폴더의 pdf파일을 청킹함)\
embedding.py 실행시\
retriever.py 실행시 data_analysis의 interest, tone, top_words, summary를 고려하여 책 가져옴

<pre>gcloud auth application-default login
pip install google-cloud-storage
pip install pymupdf
</pre>
