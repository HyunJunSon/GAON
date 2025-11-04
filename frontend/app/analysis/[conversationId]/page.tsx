// 특정 conversation에 대한 상세 페이지
// 2단계에서 TanStack Query로 GET /analysis/{conversationId} 연결
// 3단계에서 탭(/summary|/emotion|/dialog) 확장 예정

type PageProps = {
  params: {conversationId: string};
};

export default function AnalysisDetailPage({ params }: PageProps) {
  const { conversationId } = params;
  return (
    <main className="mx-auto max-w-2xl p-6">
      <header>
        <h1 className="text-2xl font-semibold mb-2">분석 결과</h1>
        <p className="text-sm text-gray-600">대화 ID:</p>
      </header>
      {/* useQuery로 상태(queued/processing/ready/failed) 표시 */}
      <section className="rounded-lg border bg-white p-4">
        <p className="text-sm text-gray-700">
          여기에서 <strong>{conversationId}</strong>에 대한 분석 상태와 결과를 표시
        </p>
        <p className="text-xs text-gray-500 mt-2">
           다음 단계에서 서버 요청/폴링을 붙이고, 준비 완료 시 요약/감정/대화록 탭을 노출할 예정입니다.
        </p>
      </section>
    </main>
  )
}