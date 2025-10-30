from deepeval.test_case import ConversationalTestCase, Turn
from deepeval.metrics import TurnRelevancyMetric, KnowledgeRetentionMetric
from deepeval import evaluate

test_case = ConversationalTestCase(turns=[
  Turn(role="user", content="(부모 역할) 공부 얘기 좀 하자."),
  Turn(role="assistant", content="(시뮬레이터 답변-모델A) ..."),
  Turn(role="user", content="내 입장도 좀 이해해줘."),
  Turn(role="assistant", content="(시뮬레이터 답변-모델A) ...")
])
evaluate([test_case], metrics=[TurnRelevancyMetric(), KnowledgeRetentionMetric()])
