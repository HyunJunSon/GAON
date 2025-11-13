'use client';

/**
 * /practice
 * - 쿼리/스토리지 등에서 conversation_id 확인
 * - 있으면 /practice/setting 으로 라우팅
 * - 없으면 안내 문구
 */
export default function PracticeEntryPage() {
  return (
    <main className="mx-auto max-w-2xl p-6 space-y-4">
      <h1 className="text-xl font-semibold">연습하기</h1>
      <p className="text-sm text-gray-600">
        최근 분석된 대화가 없어요. 먼저 대화를 업로드하고 분석을 완료한 뒤, 이곳에서 연습을 시작해 주세요.
      </p>
    </main>
  );
}