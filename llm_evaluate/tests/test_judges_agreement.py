from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import GEval
from deepeval import evaluate

outputs = [
  ("GPT-4o", open("outputs/generator_gpt4o.txt", encoding="utf-8").read()),
  ("Claude", open("outputs/generator_claude.txt", encoding="utf-8").read()),
  ("Gemini", open("outputs/generator_gemini.txt", encoding="utf-8").read()),
]

cases = [LLMTestCase(input="(대화)", actual_output=o) for _, o in outputs]

judge_a = GEval(name="QualityA", model="gpt-4o-mini",
                criteria="공감·구체성·정확성 종합평가",
                evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT])

judge_b = GEval(name="QualityB", model="claude-3-haiku-20240307",
                criteria="공감·구체성·정확성 종합평가",
                evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT])

print("=== Judge A ===")
evaluate(cases, metrics=[judge_a])
print("=== Judge B ===")
evaluate(cases, metrics=[judge_b])
