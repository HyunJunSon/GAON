from deepeval.test_case import LLMTestCase
from deepeval.metrics import ContextualRelevancyMetric, ContextualPrecisionMetric
from deepeval import evaluate

# (사전) 벡터DB 생성은 별도 스크립트에서 수행, 여기선 검색 결과만 사용한다고 가정
query = "공부 스트레스로 갈등일 때 부모의 첫 한 마디는?"
retrieved = [
  "오은영: 지적보다 공감으로 시작한다",
  "부모-자녀 갈등 시 감정 인정 표현 예시",
  "비난·단정 금지"
]

cases = [LLMTestCase(input=query, retrieval_context=retrieved)]

metrics = [
  ContextualRelevancyMetric(threshold=0.7),  # 검색문맥의 관련도
  ContextualPrecisionMetric(threshold=0.7)   # 잡음 비율
]

evaluate(cases, metrics=metrics)
