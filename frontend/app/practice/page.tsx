'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { conversationIdStorage } from '@/utils/conversationIdStorage';
import Link from 'next/link';

/**
 * /practice
 * - 쿼리/스토리지 등에서 conversation_id 확인
 * - 있으면 /practice/setting 으로 라우팅
 * - 없으면 안내 문구
 */
export default function PracticeEntryPage() {
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    // 1) 로컬 저장소 등에서 최근 conversation_id 조회
    const lastConversationId = conversationIdStorage.get();

    if (lastConversationId) {
      // 2) 있으면 바로 /practice/setting 으로 이동
      router.replace('/practice/setting?conversationId=' + encodeURIComponent(lastConversationId));
      return;
    }
    // 없으면 그냥 아래 JSX 안내문이 보이게 둔다.
    // 바로 setChecked(true)를 호출하지 않고, 다음 tick으로 살짝 미뤄서 실행
    queueMicrotask(() => {
      setChecked(true);
    });
  }, [router]);

  // ✅ 아직 체크 중이면 아무것도 안 보여주거나, 아주 간단한 로딩만 보여주기
  if (!checked) {
    return null;
    // 또는:
    // return (
    //   <main className="mx-auto max-w-2xl p-6">
    //     <p className="text-sm text-gray-500">연습 준비 상태를 확인하는 중…</p>
    //   </main>
    // );
  }
  // 여기까지 왔다는 건 → conversationId가 "없다"는 뜻
  return (
    <main className="mx-auto max-w-2xl space-y-4 p-4">
      <h1 className="text-2xl font-semibold">연습하기</h1>

      <p className="text-sm text-gray-600">
        최근 분석된 대화가 없어서 연습을 시작할 수 없어요.
      </p>

      <p className="text-sm text-gray-600">
        먼저 <strong>대화 파일을 업로드</strong>하고,{' '}
        <strong>분석 결과 페이지</strong>에서 “연습하러 가기” 버튼을 눌러주세요.
      </p>

      <div className="mt-4">
        {/* 실제 대화 업로드/분석 시작 페이지 경로에 맞게 href 수정 */}
        <Link
          href="/conversation"
          className="inline-flex items-center rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-800 hover:bg-gray-50"
        >
          대화 업로드 하러 가기
        </Link>
      </div>
    </main>
  );
}