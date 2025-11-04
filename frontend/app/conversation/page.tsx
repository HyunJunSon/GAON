// 업로드/분석 요청 페이지 스켈레톤
// 지금은 실제 업로드/분석 요청 없이 UI 골격만 표시
// 2단계에서 FormData 업로드 + 서보 호출(POST /conversations/analyze) 연결 예정

export default function ConversationPage() {
  return (
    <main className="mx-auto max-w-2xl p-6">
      <header>
        <h1 className="text-2xl font-semibold mb-2">대화 업로드</h1>
        <p className="text-sm text-gray-600">음성 파일을 선택하고 분석을 시작하세요.</p>
      </header>
      {/* [스텁] 드롭존/파일선택 영역 – 2단계에서 실제 업로드 로직 연결 */}
      <section className="rounded-lg border border-dashed border-gray-300 p-6 bg-white">
        <p className="text-sm text-gray-700">
          여기에 업로드 UI가 들어갑니다. (mp3, wav, m4a 등 / 최대 용량 안내)
        </p>
      </section>
      {/* [스텁] 분석 시작 버튼 - 2단계에서 mutation으로 교체하고, 성공 시 /analysis/[id]로 이동 */}
      <div>
        <button
          type="button"
          className="rounded bg-black px-4 py-2 text-white disabled:opacity-50"
          disabled
          aria-disabled
          title="분석 시작"
        >
          분석 시작 (2단계에서 활성화)
        </button>
      </div>
    </main>
  );
}