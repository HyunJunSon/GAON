# llm_evaluate
### evaluate process
Embedding-> Retriever -> Generator -> Judge/Evaluator -> Formatter -> Simulator

<details>
<summary>setup</summary>
<pre>pip install -U deepeval openai langchain chromadb
export OPENAI_API_KEY=sk-*** </pre>

data: oh_eunyoung.txt, family_dialogues.json

</details>

<details>
<summary>Embedding</summary>
```
목적: text-embedding-3-large 가 “의미 유사도 검색”에 적합한지 확인 (= 결과적으로 Retriever 품질로 드러남)

테스트 방식

쿼리(=대화 요약 or 핵심 질문)와 정답 근거 문단(골든)을 준비

해당 임베딩으로 만든 벡터DB에서 top-k 검색 결과를 test_case.retrieval_context에 넣고 평가

파일: tests/test_embedding_retriever.py

실행:
<pre>deepeval test run tests/test_embedding_retriever.py -v
*** </pre>

```
</details>

<details>
<summary>Retriever</summary>
```
d
```
</details>

<details>
<summary>Generator</summary>
```
d
```
</details>

<details>
<summary>Judge/Evaluator</summary>
```
d
```
</details>

<details>
<summary>Formatter</summary>
```
d
```
</details>

<details>
<summary>Simulator</summary>
```
d
```
</details>
