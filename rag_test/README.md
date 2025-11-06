# rag_test
bucket -> toc_extract ->

bucket.py 실행시 pdf변환_downloads폴더가 생기면서 gcp에있는 pdf파일 다운됨
toc_extract.py 실행시 다운받은 pdf파일의 toc(목차카탈로그)를 추출해서 toc_out 폴더의 json파일로 저장 (대분류, 중분류, 소분류, 페이지 번호 저장됨)

<pre>gcloud auth application-default login
pip install google-cloud-storage
pip install pymupdf
</pre>
