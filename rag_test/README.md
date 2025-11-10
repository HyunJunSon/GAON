# rag_test

## bucket -> toc_extract -> chunking -> embedding_save

- bucket.py\
pdf변환_downloads폴더가 생기면서 gcp에있는 pdf파일 다운됨
- toc_extract.py\
다운받은 pdf파일의 toc(목차카탈로그)를 추출해서 toc_out 폴더의 json파일로 저장 (대분류, 중분류, 소분류, 페이지 번호 저장됨)
- chunking.py\
가장 작은 목차 분류를 기준으로 600~800자 청킹-> 임베드 텍스트(대,중,소 제목 + 본문청크)저장 (toc_out폴더의 json파일을 참고해서 pdf변환_downloads폴더의 pdf파일을 청킹함)
- embedding_save.py\
임베드 텍스트를 벡터화하고 전체 jsonl을 postgresql에 저장함
$ python embedding_save.py --create-table-if-missing\
<img src="http://dev.wyhil.com:43000/SG-OHA-2025-TEAM-04/GAON/raw/branch/feature/%235/rag_test/20251107_172833.png" width="600"/>
<img src="http://dev.wyhil.com:43000/SG-OHA-2025-TEAM-04/GAON/raw/branch/feature/%235/rag_test/20251110_165042.png" width="600"/>

## summary_rag.py -> advice.py -> advice_save.py

- summary_rag.py\
analysis_result의 analysis_id 최신에 따른 summary부분만 벡터화 시켜서 ref_handbook_snippet 책의 pgvector KNN 검색 후 같은 section_id는 chunk_ix 순으로 자동 스티칭 후 상위 섹션들 프리뷰(본문 앞부분 + citation) 출력
(검색 결과 미리보기단계)
<img src="http://dev.wyhil.com:43000/SG-OHA-2025-TEAM-04/GAON/raw/branch/feature/%235/rag_test/20251107_171549.png" width="600"/>

- advice.py\
요약 임베딩 생성 → ref_handbook_snippet.embedding에 pgvector KNN 검색 → 히트된 section_id의 섹션 전체 본문을 DB에서 재조회/스티칭 → 그 풀 텍스트 문맥으로 LLM 프롬프트 구성 → 조언 + 출처 출력, 이어서 미리보기(몇 줄)만 콘솔에 표시
<img src="http://dev.wyhil.com:43000/SG-OHA-2025-TEAM-04/GAON/raw/branch/feature/%235/rag_test/20251110_133635.png" width="600"/>
<img src="http://dev.wyhil.com:43000/SG-OHA-2025-TEAM-04/GAON/raw/branch/feature/%235/rag_test/20251110_082946.png" width="600"/>
<img src="http://dev.wyhil.com:43000/SG-OHA-2025-TEAM-04/GAON/raw/branch/feature/%235/rag_test/20251110_083001.png" width="600"/>
<img src="http://dev.wyhil.com:43000/SG-OHA-2025-TEAM-04/GAON/raw/branch/feature/%235/rag_test/20251110_083014.png" width="600"/>

- advice_save.py\
analysis_result의 analysis_id에 해당하는 feedback 저장 
<img src="http://dev.wyhil.com:43000/SG-OHA-2025-TEAM-04/GAON/raw/branch/feature/%235/rag_test/20251110_090545.png" width="600"/>
<img src="http://dev.wyhil.com:43000/SG-OHA-2025-TEAM-04/GAON/raw/branch/feature/%235/rag_test/20251110_090522.png" width="600"/>

<pre>gcloud auth application-default login
pip install google-cloud-storage
pip install pymupdf
</pre>
