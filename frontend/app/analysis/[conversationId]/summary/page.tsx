'use client';

import { AnalysisRes } from "@/apis/analysis";
import { useAnalysis } from "@/hooks/useAnalysis";
import { useParams } from "next/navigation";

/* -------------------- Feedback 타입 + 유틸 -------------------- */

type FeedbackJson = {
  summary_for_client: string;
  strengths: string;
  improvements: string;
  action_steps: string;
  warnings: string;
  checklist: string | string[];
  sources: string[];
};

function parseChecklist(raw: string | string[] | undefined): string[] {
  if (!raw) return [];
  if (Array.isArray(raw)) return raw;
  return raw
    .split("\n")
    .map((line) => line.replace(/^[-•]\s*/, "").trim())
    .filter(Boolean);
}

/* -------------------- 컴포넌트 -------------------- */

export default function ResultsSummaryPage() {
  const { conversationId } = useParams();
  const id = Array.isArray(conversationId) ? conversationId[0] : (conversationId as string);
  const { data, isLoading, isError, error } = useAnalysis(id);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-orange-200 border-t-orange-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">분석 결과를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-red-600">
            {(error as Error)?.message ?? "분석 결과를 불러올 수 없습니다"}
          </p>
        </div>
      </div>
    );
  }

  if (data.status !== "ready" && data.status !== "completed") {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-orange-200 border-t-orange-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">현재 상태: {data.status}</p>
        </div>
      </div>
    );
  }

  /* -------------------- 데이터 분해 -------------------- */

  const { summary, style_analysis, score, confidence_score, feedback } = data;
  const MY_SPEAKER_ID = "1";
  const myStyle =
    (style_analysis as AnalysisRes["style_analysis"] | undefined)?.[MY_SPEAKER_ID] ?? null;

  // 🔥 로컬 UI 확인용 dummy feedback
  const dummyFeedback: FeedbackJson = {
    summary_for_client:
      "대화에서 너는 아버지와의 관계에서 느끼는 어려움과 그로 인한 통증을 솔직하게 드러내었어. 예를 들어, '아빠가 꽉 잡아서 어깨가 아파요.'라고 말하면서 너의 감정을 잘 표현했지. 그리고 여러 상황에서 문장에 오류가 없다고 확인하며 정확하게 말하려는 모습이 보였어.",
    strengths:
      "너는 대화 중 자신의 감정이나 상태를 명확하게 표현하는 데 이미 아주 잘하고 있어. 특히 '근육이 놀랐대요. 일주일 정도 움직이지 말래요.'라는 발화는 너의 상황을 진솔하게 전달했어. 또한, 대화의 흐름을 유도하면서 상대방의 질문에 간결하게 대답하며 좋은 소통을 이어갔다는 점이 인상적이야.",
    improvements:
      "앞으로는 너의 감정을 더 풍부하게 표현할 수 있도록 연습해보면 좋겠어. 예를 들어, 아버지와의 갈등에 대해 이야기할 때 단순히 아파한다고 말하기보다는 그로 인해 느끼는 감정, 예를 들어 슬픔이나 불안도 함께 표현해보는 거야. 이렇게 하면 대화의 깊이가 더해질 수 있을 거야.",
    action_steps:
      "오늘 저녁에는 가족과 대화할 때, 너의 감정에 대해 조금 더 이야기해보는 건 어때? 예를 들어, 아버지와의 갈등에 대해 이야기하면서 '가끔 아빠랑 싸울 때, 그 때문에 기분이 많이 우울해져요.'라고 말해 보는 거야. 다른 사람에게, 특히 친구나 선생님에게도 너의 기분을 솔직하게 물어보는 연습을 언제든지 해보면 좋겠어.",
    warnings:
      "지금 힘든 감정을 느끼고 있다면, 혼자 버티지 말고 주변 사람들에게 도움을 요청해야 해. 감정은 때때로 그무너질 것 같은 기분을 줄 수 있으니 필요할 때는 반드시 믿을 수 있는 사람에게 이야기하는 것이 중요해.",
    checklist:
      "- 저녁에 가족과 대화할 때 너의 감정을 솔직하게 표현해 보기\n- 친구에게 요즘 느끼는 기분을 솔직하게 이야기해보기\n- 어려운 상황에 처했을 때 믿을 수 있는 사람에게 도움 요청하기\n",
    sources: [
      "아들러 성격 상담소 - 기시미 이치로 | 장 소극적·불안함·두려움 방어형은 과제에서 도망친다 > 쉽게 불안해지는 성격, p.63-75",
      "말투에도 연습이 필요합니다 - 김현정 | 우리가 피해야 할 대화법 > 화를 표현하는 법, p.256-261",
      "말투에도 연습이 필요합니다 - 김현정 | 우리가 피해야 할 대화법 > 상대를 경멸하는 건 독이다, p.274-280",
      "마음을 훔치는 대화법 _ 이론편 - 임철웅 | 대화를 주도하는 말하기 기술 > 상대의 정보를 축적하는 비법, 질문하기 > 대화의 시작을 여는 질문하기, p.110-112",
      "말투에도 연습이 필요합니다 - 김현정 | 관계를 만드는 기적의 대화법 3 > 논리보다 감정이 중요하다, p.187-192",
      "마음을 훔치는 대화법 _ 이론편 - 임철웅 | 대화를 주도하는 말하기 기술 > 자연스러운 대화를 이끄는 질문 활용 방법 > 기억해두세요, 상황별 질문들, p.138-140",
      "마음을 훔치는 대화법 _ 이론편 - 임철웅 | 말하는 스타일에 따른 대화법 > 말하기 유형에 따라 말하는 스타일이 달라진다 > 상담가형의 특징, p.240"
    ]
  };

  const fb: FeedbackJson =
    feedback && feedback !== ""
      ? (feedback as unknown as FeedbackJson)
      : dummyFeedback;

  return (
    <main className="mx-auto max-w-4xl p-6">
      <div className="space-y-8">
        {/* 헤더 */}
        <header className="text-center">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-orange-100 to-red-100 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h1 className="text-3xl font-bold text-gray-800">분석 요약</h1>
          </div>
          
          {(score != null || confidence_score != null) && (
            <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-2xl p-6 mb-6">
              <div className="flex items-center justify-center gap-8">
                {score != null && (
                  <div className="text-center">
                    <div className="text-4xl font-bold">{(score * 100).toFixed(0)}</div>
                    <div className="text-orange-100">말하기 점수</div>
                  </div>
                )}
                {confidence_score != null && (
                  <div className="text-center">
                    <div className="text-4xl font-bold">{(confidence_score * 100).toFixed(0)}%</div>
                    <div className="text-orange-100">신뢰도</div>
                  </div>
                )}
              </div>
            </div>
          )}
        </header>

        {/* 말투/성향 분석 */}
        {!!myStyle && (
          <section className="bg-white rounded-2xl shadow-lg border border-orange-100 p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-100 to-purple-100 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900">말투/성향 분석</h3>
            </div>
            <div className="grid gap-4">
              {myStyle["주요_관심사"] && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-2">주요 관심사</h4>
                  <p className="text-gray-700">{myStyle["주요_관심사"]}</p>
                </div>
              )}
              {myStyle["대화_비교_분석"] && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-2">대화 비교 분석</h4>
                  <p className="text-gray-700">{myStyle["대화_비교_분석"]}</p>
                </div>
              )}
              {myStyle["말투_특징_분석"] && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-2">말투 특징</h4>
                  <p className="text-gray-700">{myStyle["말투_특징_분석"]}</p>
                </div>
              )}
              {myStyle["대화_성향_및_감정_표현"] && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 mb-2">성향/감정 표현</h4>
                  <p className="text-gray-700">{myStyle["대화_성향_및_감정_표현"]}</p>
                </div>
              )}
            </div>
          </section>
        )}

        {/* AI 리포트 */}
        {!!summary && (
          <section className="bg-white rounded-2xl shadow-lg border border-orange-100 p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-gradient-to-br from-green-100 to-emerald-100 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-800">AI 리포트</h3>
            </div>
            <div className="bg-gray-50 rounded-lg p-6">
              <pre className="whitespace-pre-wrap break-words text-gray-800 leading-relaxed">
                {summary.trim()}
              </pre>
            </div>
          </section>
        )}

        {/* 개선점 & 피드백 */}
        {fb && (
          <section className="bg-white rounded-2xl shadow-lg border border-orange-100 p-8 space-y-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-gradient-to-br from-yellow-100 to-orange-100 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900">개선점 & 피드백</h3>
            </div>

            {/* 요약 */}
            <div className="bg-amber-50 rounded-lg p-4 border border-amber-100">
              <h4 className="text-base font-semibold text-gray-900 mb-2">요약</h4>
              <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
                {fb.summary_for_client}
              </p>
            </div>

            {/* 강점 */}
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
              <h4 className="text-base font-semibold text-gray-900 mb-2">강점</h4>
              <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
                {fb.strengths}
              </p>
            </div>

            {/* 개선 포인트 */}
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
              <h4 className="text-base font-semibold text-gray-900 mb-2">개선 포인트</h4>
              <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
                {fb.improvements}
              </p>
            </div>

            {/* 실천 */}
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
              <h4 className="text-base font-semibold text-gray-900 mb-2">오늘 해볼 수 있는 실천</h4>
              <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
                {fb.action_steps}
              </p>
            </div>

            {/* 주의 */}
            <div className="bg-rose-50 rounded-lg p-4 border border-rose-100">
              <h4 className="text-base font-semibold text-gray-900 mb-2">주의 / 마음 건강</h4>
              <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
                {fb.warnings}
              </p>
            </div>

            {/* 체크리스트 */}
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
              <h4 className="text-base font-semibold text-gray-900 mb-3">체크리스트</h4>
              <ul className="space-y-2 text-sm">
                {parseChecklist(fb.checklist).map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <input type="checkbox" className="mt-0.5 h-4 w-4 rounded border-gray-300" />
                    <span className="text-gray-700 leading-relaxed">{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* 출처 */}
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-100">
              <h4 className="text-base font-semibold text-gray-900 mb-2">참고한 책 / 출처</h4>
              <ul className="list-disc pl-5 text-xs text-gray-700 space-y-1">
                {fb.sources.map((src, idx) => (
                  <li key={idx}>{src}</li>
                ))}
              </ul>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
