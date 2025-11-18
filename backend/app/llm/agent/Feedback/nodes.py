# backend/app/llm/agent/Feedback/nodes.py
# -*- coding: utf-8 -*-

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Any, List

import os
import json
import psycopg2
import psycopg2.extras as extras
import pandas as pd
from sqlalchemy.orm import Session
from openai import OpenAI
from langchain_openai import ChatOpenAI

from app.core.database import engine
from app.core.config import settings
from app.llm.agent.crud import get_analysis_by_conv_id, save_feedback

if TYPE_CHECKING:
    from .graph_feedback import FeedbackState

# 1️⃣ summary + 점수 로딩
@dataclass
class SummaryLoaderNode:
    verbose: bool = True

    def __call__(self, state: "FeedbackState") -> "FeedbackState":
        db: Session = state.db
        conv_id = state.conv_id

        if not db:
            raise ValueError("❌ SummaryLoaderNode: db 세션 없음")
        if not conv_id:
            raise ValueError("❌ SummaryLoaderNode: conv_id 없음")

        row = get_analysis_by_conv_id(db, conv_id)
        if not row:
            raise ValueError(f"❌ analysis_result 없음: conv_id={conv_id}")

        state.analysis_row = row
        state.analysis_id = row["analysis_id"]
        state.summary = (row.get("summary") or "").strip()
        state.score = float(row.get("score", 0.0))
        state.confidence_score = float(row.get("confidence_score", 0.0))

        if not state.summary:
            raise ValueError("❌ SummaryLoaderNode: summary 비어 있음")

        if self.verbose:
            print("\n📥 [SummaryLoaderNode] 분석 결과 로딩 완료")
            print(f"   → analysis_id: {state.analysis_id}")
            print(f"   → score={state.score:.2f}, confidence={state.confidence_score:.2f}")
            print(f"   → summary 길이={len(state.summary)}자")

        return state

# 2️⃣ summary → 책 검색용 쿼리 변환 (LLM)
@dataclass
class SummaryToBookQueryNode:
    verbose: bool = True

    def __call__(self, state: "FeedbackState") -> "FeedbackState":
        summary = state.summary

        if not summary:
            raise ValueError("❌ SummaryToBookQueryNode: summary 없음")

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.openai_api_key,
        )

        prompt = f"""
너는 상담 관련 책과 대화법 책을 잘 아는 '전문 사서'이다.

아래 텍스트는 항상 다음 구조를 가진 '대화 분석 리포트'이다:

1) 말하기 점수 / 단어 수 / 문장 길이 / 고유 단어 / 자주 쓰는 단어 등 **통계/점수**
2) 말투 분석 (예: 반말/존댓말, 표현 스타일, 문법 등)
3) 감정/성향 분석 (예: 가족에 대한 애정, 상실감, 불안, 우울, 분노, 회피, 개방성 등)
4) 종합 평가 (강점 / 개선점 / 추천 사항)

[대화 분석 리포트]
\"\"\"{summary}\"\"\"

임베딩된 책 텍스트는 항상 다음과 같은 형식을 가진다:

[대제목 > 중제목 > 소제목] 본문 내용...

따라서, 네가 만들어야 할 검색 쿼리도 다음과 같은 구조여야 한다:

- 한 줄: '대제목 또는 (대제목 > 중제목)처럼 쓸 수 있는 짧은 제목 문장'
- 그 아래: 관련된 상담/대화 상황을 2~4문장 정도로 설명하는 본문

### 1) counsel_query (상담책용)
- 이 내담자의 심리, 감정 패턴, 관계, 상실·불안·애착, 예민함 등을 반영해
  '상담/심리 책의 장 제목 + 본문'처럼 쿼리를 만들어라.

예시 스타일:
"형제 상실을 겪은 아이의 애도와 가족에 대한 불안
언니를 교통사고로 잃은 아이가 가족과의 일상 대화에서는 밝고 잘 지내는 모습을 보이지만, 마음 한편으로는 부모가 자신을 떠날까 걱정하며 악몽과 가슴 두근거림을 겪고 있다. 이런 아이의 슬픔과 불안을 어떻게 이해하고, 애도 과정과 애착을 다루어 줄 것인지에 대한 상담 이론과 사례가 필요하다."

### 2) talk_query (대화책용)
- 이 내담자와 대화할 때 필요한 말하기/듣기/질문 기술을,
  '대화법 책의 장 제목 + 본문'처럼 쿼리로 만들어라.

예시 스타일:
"상실을 경험한 아이에게 안전감을 주는 질문과 공감 대화법
언니를 잃은 이후 부모를 잃을까 걱정하지만 겉으로는 밝게 지내는 아이에게, 상담자나 부모가 어떤 말투와 질문으로 마음을 열게 도와줄 수 있을지 고민된다. 아이가 느끼는 슬픔과 불안을 존중하면서도 긍정적인 경험(가족과의 시간, 친구와의 놀이, 유튜브 꿈)을 활용해 안전감을 전하고, 감정을 말로 표현하는 연습을 돕는 구체적인 공감·경청·질문 대화법이 필요하다."

주의:
- 점수/단어 수/문장 길이 같은 통계는 무시하고,
  감정·성향·강점·개선점 설명에만 집중해서 주제를 뽑아라.
- 반드시 아래 JSON 형식으로 답해야 한다:

{{
  "counsel_query": "상담책 검색용: [제목\\n본문...] 형태의 문자열",
  "talk_query": "대화책 검색용: [제목\\n본문...] 형태의 문자열"
}}
"""

        if self.verbose:
            print("\n🧠 [SummaryToBookQueryNode] 책 검색용 쿼리 생성 중...")

        resp = llm.invoke(prompt)
        content = resp.content if hasattr(resp, "content") else str(resp)

        try:
            content = content.strip()

            # 1) "json\n{...}" 형식 처리
            if content.lower().startswith("json"):
                # 첫 줄 "json" 떼고 나머지 전체
                parts = content.split("\n", 1)
                if len(parts) == 2:
                    content = parts[1].strip()

            # 2) ```json ... ``` 같은 코드블록 처리
            if "```" in content:
                # 예: ```json\n{...}\n``` 형태 → 중간 부분만
                chunks = content.split("```")
                # 길이에 따라 안전하게 가운데 JSON 부분을 고르기
                if len(chunks) >= 3:
                    content = chunks[1].strip()
                else:
                    content = chunks[-1].strip()

            data = json.loads(content)
        except Exception as e:
            print(f"   ❌ JSON 파싱 실패: {e}")
            print(f"   원본 응답 일부: {content[:200]}...")
            data = {
                "counsel_query": summary,
                "talk_query": summary,
            }

        state.counsel_query = (data.get("counsel_query") or summary).strip()
        state.talk_query = (data.get("talk_query") or summary).strip()

        if self.verbose:
            print("   ✅ counsel_query:", state.counsel_query[:80], "...")
            print("   ✅ talk_query:", state.talk_query[:80], "...")

        return state

# 3️⃣ ideal_answer에서 상담/대화법 RAG + JSON 조언 + feedback 저장
@dataclass
class RAGAndAdviceNode:
    verbose: bool = True

    def _make_query_embedding(self, client: OpenAI, text: str, model="text-embedding-3-small") -> list:
        t = (text or "").strip()
        if not t:
            raise ValueError("query is empty")
        return client.embeddings.create(model=model, input=[t]).data[0].embedding

    def _knn_search(
        self,
        conn,
        qvec: list,
        table: str,
        limit: int = 50,
        for_counsel: bool | None = None,
    ):
        # for_counsel:
        #   True  → 상담 책만
        #   False → 상담 아닌 책만
        #   None  → 전체
        where = ""
        if for_counsel is True:
            where = "WHERE book_title LIKE '%%상담%%'"
        elif for_counsel is False:
            where = "WHERE (book_title NOT LIKE '%%상담%%' OR book_title IS NULL)"

        sql = f"""
          SELECT snippet_id,
                 section_id,
                 canonical_path,
                 chunk_ix,
                 page_start,
                 page_end,
                 citation,
                 full_text,
                 book_title,
                 (embedding <=> %s::vector) AS distance
          FROM {table}
          {where}
          ORDER BY distance
          LIMIT %s
        """
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            # ⚠️ 여기 파라미터는 두 개만!
            cur.execute(sql, (qvec, limit))
            return cur.fetchall()

    def _fetch_full_sections(self, conn, table: str, section_ids: list[str]) -> list[dict]:
        if not section_ids:
            return []

        sql = f"""
          SELECT section_id, canonical_path, chunk_ix,
                 page_start, page_end, citation, full_text, book_title
          FROM {table}
          WHERE section_id = ANY(%s)
          ORDER BY section_id, chunk_ix, page_start, page_end
        """
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(sql, (section_ids,))
            rows = cur.fetchall()

        by: Dict[str, Any] = {}
        for r in rows:
            g = by.setdefault(r["section_id"], {
                "section_id": r["section_id"],
                "canonical_path": r["canonical_path"],
                "book_title": r.get("book_title"),
                "snippets": [],
                "citations": set(),
            })
            g["snippets"].append(r)
            if r.get("citation"):
                g["citations"].add(r["citation"])

        sections = []
        for sec in by.values():
            text = "\n\n".join(x["full_text"] for x in sec["snippets"] if x.get("full_text"))
            sections.append({
                "section_id": sec["section_id"],
                "canonical_path": sec["canonical_path"],
                "book_title": sec["book_title"],
                "text": text.strip(),
                "citations": sorted(sec["citations"]),
            })
        return sections

    def _build_sections_with_filter(
        self,
        qvec: list,
        table: str,
        sim_threshold: float,
        for_counsel: bool | None = None,
    ) -> List[Dict[str, Any]]:
        conn = engine.raw_connection()
        try:
            rows = self._knn_search(conn, qvec, table=table, limit=50, for_counsel=for_counsel)
        finally:
            conn.close()

        if self.verbose:
            print(f"\n🔎 [RAG] knn 결과 {len(rows)}개 (for_counsel={for_counsel})")
            for r in rows[:10]:
                d = float(r["distance"])
                sim = 1.0 - d
                print(
                    f"   section_id={r['section_id']}, "
                    f"book_title={r.get('book_title')}, "
                    f"distance={d:.4f}, sim={sim:.4f}"
                )

        filtered_ids = set()
        best_dist_map: Dict[str, float] = {}

        for r in rows:
            d = r.get("distance")
            if d is None:
                continue
            d = float(d)
            sim = 1.0 - d

            if sim < sim_threshold:
                continue

            sid = r["section_id"]
            filtered_ids.add(sid)
            if sid not in best_dist_map or d < best_dist_map[sid]:
                best_dist_map[sid] = d

        if self.verbose:
            print(f"   🔍 sim_threshold={sim_threshold}, 통과 section 수={len(filtered_ids)}")

        if not filtered_ids:
            return []

        conn2 = engine.raw_connection()
        try:
            sections = self._fetch_full_sections(conn2, table, sorted(filtered_ids))
        finally:
            conn2.close()

        for s in sections:
            s["best_dist"] = best_dist_map.get(s["section_id"])

        sections.sort(
            key=lambda z: (
                float("inf") if z.get("best_dist") is None else z["best_dist"]
            )
        )
        return sections[:6]


    def __call__(self, state: "FeedbackState") -> "FeedbackState":
        API_KEY = os.getenv("OPENAI_API_KEY") or settings.openai_api_key
        TABLE   = os.getenv("IDEAL_ANSWER_TABLE") or "ideal_answer"
        SIM_TH  = float(os.getenv("RAG_SIM_THRESHOLD") or 0.45)  # 유사도 0.45 이상만 사용

        if not API_KEY:
            raise ValueError("❌ OPENAI_API_KEY 필요")

        analysis_id = state.analysis_id
        summary = state.summary
        counsel_query = state.counsel_query or summary
        talk_query = state.talk_query or summary
        db: Session = state.db
        conversation_df = state.conversation_df

        if not analysis_id:
            raise ValueError("❌ RAGAndAdviceNode: analysis_id 없음")
        if not summary:
            raise ValueError("❌ RAGAndAdviceNode: summary 없음")
        if not db:
            raise ValueError("❌ RAGAndAdviceNode: db 세션 없음")

        client = OpenAI(api_key=API_KEY)

        # 1) 쿼리 임베딩
        qvec_counsel = self._make_query_embedding(client, counsel_query)
        qvec_talk    = self._make_query_embedding(client, talk_query)

        # 2) ideal_answer에서 섹션 가져오기 (유사도 0.45 이상만)
        sections_cand_counsel = self._build_sections_with_filter(
            qvec_counsel, TABLE, SIM_TH, for_counsel=True
        )
        sections_cand_talk    = self._build_sections_with_filter(
            qvec_talk,    TABLE, SIM_TH, for_counsel=False
        )
        
        # 3)이제는 이미 KNN에서 상담/비상담 나눠졌으니까 그대로 씀
        counsel_sections = sections_cand_counsel
        talk_sections    = sections_cand_talk

        state.counsel_sections = counsel_sections
        state.talk_sections    = talk_sections

        # 4) 컨텍스트 문자열 만들기
        def ctx_block(prefix: str, sections: List[Dict[str, Any]]) -> str:
            if not sections:
                return f"(관련 {prefix} 문맥 없음)"
            blocks = []
            for i, s in enumerate(sections, 1):
                txt = s["text"]
                cite = "; ".join(s["citations"]) or "(no explicit page)"
                title = s.get("book_title") or ""
                blocks.append(
                    f"[{prefix} Context {i}] {title} / {s['canonical_path']}\n"
                    f"{txt}\n(출처: {cite})"
                )
            return "\n\n".join(blocks)

        counsel_ctx_str = ctx_block("상담", counsel_sections)
        talk_ctx_str    = ctx_block("대화", talk_sections)

        # 5) LLM JSON 조언 생성
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=API_KEY)

        if conversation_df is not None and not conversation_df.empty:
            conv_text = "\n".join(
                f"[참석자 {row['speaker']}] {row['text']}"
                for _, row in conversation_df.iterrows()
            )[:4000]
        else:
            conv_text = "(원본 대화는 생략됨)"

        prompt = f"""
당신은 상담 전문가입니다.
지금 만드는 리포트는
'내담자에게 들려줄 수 있는 피드백'을 정리한 것입니다.

[내담자 관점 대화 요약]
{summary}

[원본 대화 일부]
아래는 실제 대화의 중요한 일부입니다. 조언을 만들 때 여기서 드러나는 말투, 감정, 상호작용을 반드시 반영하세요.

\"\"\"{conv_text}\"\"\"

[상담/심리 문맥]
{counsel_ctx_str}

[대화 기술/표현 문맥]
{talk_ctx_str}

--------------------------------
작성 목표
--------------------------------
1) 내담자가 자신의 상태, 감정, 강점을 '스스로 이해'할 수 있게 도와준다.
2) 당장 일상에서 써먹을 수 있는 '구체적인 말/행동 연습'을 제안한다.
3) 책에서 가져온 상담/대화 이론은 참고만 하고, 
   내담자의 실제 대화 내용과 상황에 꼭 맞게 재구성한다.

--------------------------------
작성 원칙
--------------------------------
- 1차 기준은 [내담자 관점 대화 요약]과 [원본 대화 일부]입니다.
  [상담/심리 문맥], [대화 기술/표현 문맥]은 
  설명을 더 깊고 구체적으로 만들기 위한 참고 자료로 사용하세요.
- 말투:
  - 기본적으로 '너'를 주어로 쓰는 따뜻한 반말 상담 톤을 사용하세요.
  - 다만, 내담자가 부모/성인으로 추론되면 존댓말(예: "~하시는 점이 참 좋으세요.")로 자연스럽게 바꿔 쓰세요.
- 비난/판단/낙인은 절대 금지:
  - "문제가 있다", "잘못하고 있다" 대신
    "이미 ~를 잘하고 있고, 앞으로는 ~를 연습해 보면 좋겠다"처럼 제안형으로 표현하세요.
- 위험 신호(극심한 우울, 자해/자살 생각, 심한 공포 등)가 암시될 경우,
  "warnings"에 '혼자 버티지 말고 도움을 요청해야 한다'는 안전 안내를 꼭 포함하세요.
- [대화 기술/표현 문맥]은 특히 "improvements", "action_steps", "checklist"에서
  바로 따라 할 수 있는 문장/질문 예시를 만들 때 적극적으로 활용하세요.

주의:
- 예시 JSON의 설명 문장을 그대로 복사하거나 비슷하게 변형하지 마세요.
- 실제 답변에서는 반드시 이 내담자의 대화 내용, 감정, 상황을 반영한 '새로운 문장'을 작성해야 합니다.
- summary_for_client, strengths, improvements, action_steps, warnings, checklist 모두에서
  최소 한 번 이상 [내담자 관점 대화 요약] 또는 [원본 대화 일부]의 구체적인 상황을 언급하세요.
- [상담/심리 문맥], [대화 기술/표현 문맥]에 등장하는 개념이나 아이디어를,
  책 제목/페이지를 언급하지 않고 내담자에게 맞게 풀어서 설명하는 문장을 적어도 한 문장 이상 포함하세요.

위 정보를 바탕으로 아래 JSON 형식으로만 답변하세요.

--------------------------------
출력 형식 (JSON)
--------------------------------
반드시 아래 JSON 형식으로만 답변하세요.
JSON 바깥에는 어떤 텍스트도 쓰지 마세요.

각 필드는 한국어로 작성하며, 예시는 '형식과 수준'만 참고하세요.

{{
  "summary_for_client": "이 대화에서 드러난 내담자의 상황과 감정을, 내담자에게 직접 말해주는 톤으로 3~6문장으로 요약하세요. 반드시 구체적인 상황 1~2개(예: '엄마와의 통화에서 ~라고 말했을 때')를 포함해야 합니다.",
  "strengths": "이 내담자가 실제 대화에서 이미 잘하고 있는 점 2~3가지를 한 문단으로 작성하세요. 반드시 [원본 대화 일부]에서 관찰된 행동이나 말을 예로 들면서 칭찬해야 합니다.",
  "improvements": "앞으로 연습해 보면 좋을 점을 2~4문장으로 작성하세요. '무엇을 바꾸어야 한다'가 아니라 '무엇을 연습하면 더 편해질지'에 초점을 맞추고, 가능한 한 구체적인 상황을 예로 드세요.",
  "action_steps": "내담자가 일상에서 바로 해볼 수 있는 아주 구체적인 행동/말 연습을 2~4문장으로 작성하세요. '언제, 누구에게, 어떤 말/행동을'까지 명확하게 적어야 하며, [원본 대화 일부]와 자연스럽게 연결되어야 합니다.",
  "warnings": "내담자가 스스로를 지키기 위해 기억하면 좋은 주의사항을 1~3문장으로 작성하세요. 만약 대화에서 극심한 우울, 자해/자살 생각, 공포 등이 암시되었다면 반드시 '혼자 버티지 말고 도움을 요청해야 한다'는 메시지를 포함하세요.",
  "checklist": "내담자가 연습 모드에서 체크해 볼 수 있는 아주 구체적인 행동 항목 3개를 줄바꿈으로 구분해 적으세요. 각 항목은 '- '로 시작하고, [action_steps]와 연결된 행동이어야 합니다.",
  "sources": []
}}

규칙 정리:
- 반드시 위 JSON 구조와 동일한 키 이름을 사용하세요.
- 값은 모두 문자열이어야 하며, "sources"만 반드시 리스트([]) 형태로 두세요.
- 줄바꿈이 필요하면 문자열 안에 그대로 줄바꿈을 사용해도 됩니다.
- JSON 외의 다른 설명, 주석, 인삿말은 절대 쓰지 마세요.
"""

        if self.verbose:
            print("\n🧠 [RAGAndAdviceNode] JSON 조언 생성 중...")

        resp = llm.invoke(prompt)
        content = resp.content if hasattr(resp, "content") else str(resp)

        # 6) JSON 파싱
        try:
            content = content.strip()
            if "```" in content:
                content = content.split("```")[1].strip()
            advice_obj = json.loads(content)
        except Exception as e:
            print(f"   ❌ JSON 파싱 실패: {e}")
            print(f"   원본 응답 일부: {content[:200]}...")
            advice_obj = {
                "summary_for_client": summary,
                "strengths": [],
                "improvements": [],
                "action_steps": [],
                "warnings": [],
                "checklist": [],
                "sources": [],
            }

        # 7) ideal_answer 기반 실제 sources 생성
        sources: List[str] = []
        seen: set[tuple] = set()

        def collect_sources(sections: List[Dict[str, Any]]):
            for s in sections:
                book_title = (s.get("book_title") or "").strip()
                path = (s.get("canonical_path") or "").strip()
                cites = s.get("citations") or []

                # 아무 정보도 없으면 스킵
                if not book_title and not path and not cites:
                    continue

                if cites:
                    for c in cites:
                        c = (c or "").strip()
                        key = (book_title, path, c)
                        if key in seen:
                            continue
                        seen.add(key)
                        if path:
                            label = f"{book_title} | {path} | {c}"
                        else:
                            label = f"{book_title} | {c}" if book_title else c
                        sources.append(label)
                else:
                    key = (book_title, path, None)
                    if key in seen:
                        continue
                    seen.add(key)
                    label = f"{book_title} | {path}" if path else book_title
                    if label:
                        sources.append(label)

        collect_sources(counsel_sections)
        collect_sources(talk_sections)

        advice_obj["sources"] = sources

        advice_json_str = json.dumps(advice_obj, ensure_ascii=False, indent=2)

        if self.verbose:
            print("   ✅ 조언(JSON) 생성 완료 (앞 200자):")
            print(advice_json_str[:200], "...")

        # 8) feedback 컬럼에 JSON 문자열 저장
        saved = save_feedback(
            db=db,
            analysis_id=analysis_id,
            feedback=advice_json_str,
        )

        if not saved:
            raise ValueError(f"❌ feedback 업데이트 실패: analysis_id={analysis_id}")

        if self.verbose:
            print("\n💾 [RAGAndAdviceNode] feedback(JSON) 저장 완료")
            print(f"   → analysis_id: {saved['analysis_id']}")
            print(f"   → feedback 길이: {len(saved['feedback'])}자")

        state.advice_text = advice_json_str
        state.save_result = saved

        return state

