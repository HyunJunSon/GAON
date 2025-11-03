'use client';

import Link from "next/link";
import { useLogout } from "@/hooks/useAuth";

export default function HomePage() {
  const { mutate, isPending } = useLogout();

  return (
    <main className="mx-auto max-w-2xl p-6 space-y-4">
      <h1 className="text-2xl font-semibold">홈</h1>
      <div className="grid gap-3">
        <Link href="/conversation" className="underline">대화 탭으로 이동</Link>
        <Link href="/analysis/summary" className="underline">분석결과(요약)으로 이동</Link>
      </div>
      <button
      onClick={() => mutate()}
      disabled={isPending}
      className="text-sm text-gray-600 underline"
    >
      {isPending ? '로그아웃 중…' : '로그아웃'}
    </button>
    </main>
  )
}