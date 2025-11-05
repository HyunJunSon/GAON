// 분석 상세 페이지의 로딩 상태 스켈레톤
// 동적 세그먼트 로딩 중 자동으로 이 파일을 렌더

export default function AnalysisDetailLoading() {
  return (
    <div className="mx-auto max-w-2xl p-6">
      <div className="h-6 w-40 rounded bg-gray-200 animate-pulse" />
      <div className="h-4 w-64 rounded bg-gray-200 animate-pulse" />
      <div className="h-24 w-full rounded bg-gray-200 animate-pulse" />
    </div>
  )
}