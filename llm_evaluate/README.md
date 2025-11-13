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
목적: text-embedding-3-large 가 “의미 유사도 검색”에 적합한지 확인 (= 결과적으로 Retriever 품질로 드러남)

테스트 방식

쿼리(=대화 요약 or 핵심 질문)와 정답 근거 문단(골든)을 준비

해당 임베딩으로 만든 벡터DB에서 top-k 검색 결과를 test_case.retrieval_context에 넣고 평가

파일: tests/test_embedding_retriever.py

실행:
<pre>deepeval test run tests/test_embedding_retriever.py -v</pre>

👉 임베딩 모델 교체 테스트: 동일 코드에서 생성한 벡터DB만 바꿔 돌려 점수 비교(OpenAI vs Gemini Embedding 등).
</details>

<details>
<summary>Retriever</summary>
목적: 같은 임베딩이라도 검색 전략/파라미터(k, rerank) 가 맞는지 검증

트레이싱으로 컴포넌트 평가

@observe(metrics=[ContextualRelevancyMetric()]) 를 retriever 함수에 부착

함수 내부에서 update_current_span(test_case=LLMTestCase(...)) 로 retrieval_context 기록

파일: tests/test_retriever_component.py

실행:
<pre>python tests/test_retriever_component.py</pre>

</details>

<details>
<summary>Generator</summary>
목적: GPT-4o / Claude / Gemini 중 누가 “대화 분석·조언”을 더 잘 생성하는지

메트릭

Faithfulness: 답이 검색 문맥에 기반했나

Answer Relevancy: 질문/대화와 관련 있나

GEval(커스텀): 공감(Empathy)·구체성(Actionability) 채점

파일: tests/test_generator_models.py

실행:
<pre>deepeval test run tests/test_generator_models.py -v</pre>

👉 평균 점수로 Generator 우승 결정.

</details>

<details>
<summary>Judge/Evaluator</summary>
목적: 심판 LLM 후보(GPT-4o mini vs Claude Haiku) 의 일관성/안정성 비교

방법

동일한 cases에 대해 두 심판으로 각각 평가 → 점수 상관(Spearman)·재현성(재실행 분산)·에러율(429/JSON 실패) 로그 비교

파일: tests/test_judges_agreement.py

👉 두 채점표의 순위/상관을 보고 심판 채택.

</details>

<details>
<summary>Formatter</summary>
목적: 보고서 가독성/구조 준수/JSON 포맷 정확성

메트릭 아이디어

GEval(Clarity/Structure): “요약→진단→제안→점수” 구조 준수

JSON Correctness (출력을 JSON으로 강제하는 경우)

Hallucination/Consistency: 보고서의 근거 일치

파일: tests/test_formatter_quality.py


</details>

<details>
<summary>Simulator</summary>
목적: 보고서 가독성/구조 준수/JSON 포맷 정확성

메트릭 아이디어

GEval(Clarity/Structure): “요약→진단→제안→점수” 구조 준수

JSON Correctness (출력을 JSON으로 강제하는 경우)

Hallucination/Consistency: 보고서의 근거 일치

파일: tests/test_formatter_quality.py

👉 동일 스크립트를 모델A/B/C 출력으로 각각 돌려 점수 비교 + 별도 로깅으로 평균 응답시간도 함께 비교.

</details>
