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
  }

  // 여기까지 왔다는 건 → conversationId가 "없다"는 뜻
  return (
    <main className="mx-auto max-w-4xl p-6">
      <div className="flex items-center justify-center min-h-[500px]">
        <div className="text-center space-y-8">
          {/* 헤더 */}
          <div className="space-y-4">
            <div className="w-20 h-20 bg-gradient-to-br from-purple-100 to-pink-100 rounded-2xl flex items-center justify-center mx-auto">
              <svg className="w-10 h-10 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <h1 className="text-4xl font-bold text-gray-800">연습하기</h1>
            <p className="text-xl text-gray-600">대화 분석을 통한 맞춤형 연습</p>
          </div>

          {/* 안내 메시지 */}
          <div className="bg-white rounded-2xl shadow-lg border border-orange-100 p-8 max-w-md mx-auto">
            <div className="w-16 h-16 bg-gradient-to-br from-orange-100 to-red-100 rounded-xl flex items-center justify-center mx-auto mb-6">
              <svg className="w-8 h-8 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            
            <h2 className="text-xl font-semibold text-gray-800 mb-4">연습을 시작하려면</h2>
            
            <div className="space-y-4 text-gray-600">
              <p className="leading-relaxed">
                최근 분석된 대화가 없어서 연습을 시작할 수 없습니다.
              </p>
              
              <div className="bg-gray-50 rounded-xl p-4">
                <p className="text-sm leading-relaxed">
                  먼저 <span className="font-semibold text-gray-800">대화 파일을 업로드</span>하고,{' '}
                  <span className="font-semibold text-gray-800">분석 결과 페이지</span>에서 "연습하러 가기" 버튼을 눌러주세요.
                </p>
              </div>
            </div>
          </div>

          {/* 액션 버튼 */}
          <div>
            <Link
              href="/conversation"
              className="inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-orange-500 to-red-500 text-white font-semibold rounded-xl hover:from-orange-600 hover:to-red-600 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-1"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              대화 업로드 하러 가기
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
