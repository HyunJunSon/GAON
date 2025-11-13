from deepeval.tracing import observe, update_current_span
from deepeval.test_case import LLMTestCase
from deepeval.metrics import ContextualRelevancyMetric, ContextualPrecisionMetric
from deepeval.dataset import EvaluationDataset, Golden

ctx_rel = ContextualRelevancyMetric(threshold=0.7)
ctx_prec = ContextualPrecisionMetric(threshold=0.7)

@observe(metrics=[ctx_rel, ctx_prec])
def retriever(query):
    # 실제 벡터DB 검색 로직
    retrieved = ["공감으로 시작", "감정인정 표현", "비난금지"]
    update_current_span(test_case=LLMTestCase(input=query, retrieval_context=retrieved))
    return retrieved

dataset = EvaluationDataset(goldens=[Golden(input="부모의 첫 한마디는?")])
for g in dataset.evals_iterator():
    retriever(g.input)
