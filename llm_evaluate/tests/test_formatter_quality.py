from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import GEval
from deepeval import evaluate

report = open("outputs/report_gpt4o.txt", encoding="utf-8").read()
clarity = GEval(
  name="ClarityStructure",
  model="gpt-4o-mini",
  criteria="보고서가 (요약→문제패턴→개선문장→합의안→점수) 구조로 명확히 정리됐는지 평가.",
  evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT]
)
evaluate([LLMTestCase(input="N/A", actual_output=report)], metrics=[clarity])
