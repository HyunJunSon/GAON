'use client';

import { useAnalysis } from "@/hooks/useAnalysis";
// app/(main)/analysis/page.tsx
// [1단계: 라우팅만] /analysis 기본 진입 페이지
// - 특정 conversationId 없이 접근했을 때의 안내용.
// - 3단계(탭 작업) 전에 간단 가이드를 제공하고, 나중에 "최근 분석 이동" UI를 추가할 수 있습니다.

import { conversationIdStorage } from "@/utils/conversationIdStorage";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";



export default function AnalysisIndexPage() {
  const router = useRouter();
  const [id, setId] = useState<string | null>(() => conversationIdStorage.get());  
  // id가 null일 수 있으므로 빈 문자열로 대체하여 훅 호출 순서를 유지합니다.
  const safeId = id ?? '';
  const { data, isLoading, isError, error } = useAnalysis(safeId);

  // 준비 완료면 탭으로 이동 (기본: summary)
  useEffect(() => {
    if (data?.status === 'ready') {
      router.replace(`/analysis/${id}/summary`);
    }
  }, [data?.status, id, router]);

  // id 없으면 가이드 노출
  if (!id) {
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

  // 로딩/에러/상태별 안내
  if (isLoading) {
    return (
      <div className="space-y-4 p-4">
        <div className="h-6 w-40 rounded bg-gray-200 animate-pulse" />
        <div className="h-4 w-64 rounded bg-gray-200 animate-pulse" />
        <div className="h-24 w-full rounded bg-gray-200 animate-pulse" />
      </div>
    );
  }

  if (isError || !data) {
    // 404 등으로 아예 못 가져온다면 저장소 정리 + 가이드로 회귀하는 것도 방법
    return (
      <main className="space-y-4">
        <h1 className="text-2xl font-semibold">분석</h1>
        <div className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {(error as Error)?.message ?? '결과를 불러오지 못했습니다.'}
        </div>
        <button
          type="button"
          onClick={() => { conversationIdStorage.clear(); setId(null); }}
          className="rounded border px-3 py-2 text-sm"
        >
          최근 분석 ID 지우기
        </button>
      </main>
    );
  }

  // queued / processing / failed 안내 (폴링은 useAnalysis에 이미 내장)
  if (data.status !== 'ready') {
    return (
      <main className="space-y-6">
        <header>
          <h1 className="text-2xl font-semibold">분석</h1>
          <p className="text-sm text-gray-600">
            대화 ID: <code className="rounded bg-gray-100 px-1 py-0.5">{id}</code>
          </p>
        </header>

        <section className="rounded-lg border bg-white p-4">
          <p className="text-sm text-gray-700">
            현재 상태: <strong>{data.status}</strong>
          </p>
          {data.status === 'failed' && (
            <p className="text-xs text-red-600 mt-1">
              처리에 실패했습니다. 다시 시도하거나 다른 파일로 분석을 시작해 주세요.
            </p>
          )}
        </section>
      </main>
    );
  }

  // ready면 위 useEffect에서 summary로 이동하므로 여기까지 안 옴
  return null;
}