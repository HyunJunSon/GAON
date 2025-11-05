// app/(main)/analysis/page.tsx
// [1단계: 라우팅만] /analysis 기본 진입 페이지
// - 특정 conversationId 없이 접근했을 때의 안내용.
// - 3단계(탭 작업) 전에 간단 가이드를 제공하고, 나중에 "최근 분석 이동" UI를 추가할 수 있습니다.

import Link from "next/link";

export const metadata = {
  title: '분석 · GAON',
};

export default function AnalysisIndexPage() {
  return (
    <main className="space-y-4">
      <h1 className="text-2xl font-semibold">분석</h1>
      <p className="text-sm text-gray-600">
        먼저 대화 파일을 업로드하고 분석을 시작하세요. 분석이 시작되면 conversation-id로 결과를 조회할 수 있습니다.
      </p>
      <ul className="list-disc pl-5 text-sm text-gray-700 space-y-1">
        <li>
          <Link href="/conversation" className="font-medium text-blue-600 hover:underline">
            <strong>대화 페이지</strong>
          </Link>에서 파일 업로드 & 분석 시작</li>
        <li>성공 시 <strong>분석 결과 페이지</strong>로 자동 이동</li>
        <li>해당 페이지에서 분석 상태(대기/진행/완료)를 확인</li>
      </ul>
    </main>
  );
}