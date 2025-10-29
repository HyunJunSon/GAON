import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-2xl p-6 space-y-4">
      <h1 className="text-2xl font-semibold">홈</h1>
      <div className="grid gap-3">
        <Link href="/conversation" className="underline">대화 탭으로 이동</Link>
        <Link href="/results/summary" className="underline">분석결과(요약)으로 이동</Link>
      </div>
    </main>
  )
}