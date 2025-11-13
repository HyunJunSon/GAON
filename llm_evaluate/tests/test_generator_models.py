from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric, GEval
from deepeval import evaluate

conversation = "엄마: 지금 시험기간 아니야?... 아들: (울컥)..."
retrieval = ["공감으로 시작", "감정 인정", "비난 금지"]
expected = "공감→요청→합의로 수렴하는 바람직한 대화"

# 각 후보 LLM의 출력은 사전 수집 또는 코드 내에서 생성해 파일 저장 후 불러오기
gpt_output     = open("outputs/generator_gpt4o.txt", encoding="utf-8").read()
claude_output  = open("outputs/generator_claude.txt", encoding="utf-8").read()
gemini_output  = open("outputs/generator_gemini.txt", encoding="utf-8").read()

empathy = GEval(
  name="Empathy",
  model="gpt-4o-mini",
  criteria="공감·존중·경청 표현의 질을 평가하라.",
  evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
)
actionability = GEval(
  name="Actionability",
  model="gpt-4o-mini",
  criteria="실행 가능한 제안/대화문장을 얼마나 구체적으로 제시했는지.",
  evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
)
faith = FaithfulnessMetric(model="gpt-4o-mini", threshold=0.7)
rel   = AnswerRelevancyMetric(model="gpt-4o-mini", threshold=0.7)

cases = [
  LLMTestCase(input=conversation, actual_output=gpt_output,    retrieval_context=retrieval, expected_output=expected),
  LLMTestCase(input=conversation, actual_output=claude_output, retrieval_context=retrieval, expected_output=expected),
  LLMTestCase(input=conversation, actual_output=gemini_output, retrieval_context=retrieval, expected_output=expected),
]

evaluate(cases, metrics=[empathy, actionability, faith, rel])
