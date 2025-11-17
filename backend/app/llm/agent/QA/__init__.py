"""QA 모듈 초기화

`QAGraph`를 노출합니다. 간단한 run() 스텁만 제공하여 다른 코드에서
호출 가능하도록 합니다.
"""

from .graph_qa import QAGraph

__all__ = ["QAGraph"]
