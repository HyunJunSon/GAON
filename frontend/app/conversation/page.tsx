'use client';
// 업로드/분석 요청 페이지 스켈레톤
// 지금은 실제 업로드/분석 요청 없이 UI 골격만 표시
// 2단계에서 FormData 업로드 + 서보 호출(POST /conversations/analyze) 연결 예정

import { useRef, useState } from 'react';
import { startAnalysis } from '@/apis/analysis';
import { useRouter } from 'next/navigation';

const ACCEPT = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav', 'audio/m4a'];
const MAX_MB = 25;

export default function ConversationPage() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const onPick = () => inputRef.current?.click();

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    const f = e.target.files?.[0] || null;
    if (!f) return setFile(null);

    if (ACCEPT.length && !ACCEPT.includes(f.type)) {
      setError('지원하지 않는 파일 형식입니다. (mp3, wav, m4a)');
      e.target.value = '';
      return;
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      setError(`파일 용량이 너무 큽니다. (최대 ${MAX_MB}MB)`);
      e.target.value = '';
      return;
    }
    setFile(f);
  };

  const onStart = async () => {
    if (!file) return;
    setPending(true);
    setError(null);
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('lang', 'ko'); // 옵션 예시
      const res = await startAnalysis(fd);
      // 방어: snake_case 혼용 대비
      const id = (res as any)?.conversationId ?? (res as any)?.conversation_id;
      if (!id) throw new Error('서버에서 conversationId를 받지 못했습니다.');
      router.replace(`/analysis/${id}`);
    } catch (e: any) {
      setError(e?.message ?? '분석 시작에 실패했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setPending(false);
    }
  };

  return (
    <main className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">대화 업로드</h1>
        <p className="text-sm text-gray-600">음성 파일을 선택하고 분석을 시작하세요.</p>
      </header>

      {error && (
        <div className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <section className="rounded-lg border border-dashed border-gray-300 p-6 bg-white">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onPick}
            className="rounded border px-3 py-2 text-sm hover:bg-gray-50"
          >
            파일 선택
          </button>
          <input
            ref={inputRef}
            type="file"
            accept=".mp3,.wav,.m4a,audio/*"
            className="hidden"
            onChange={onFileChange}
          />
          <span className="text-sm text-gray-700">
            {file ? `${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)` : '선택된 파일 없음'}
          </span>
        </div>
        <p className="mt-2 text-xs text-gray-500">
          지원 형식: mp3, wav, m4a · 최대 {MAX_MB}MB
        </p>
      </section>

      <div>
        <button
          type="button"
          onClick={onStart}
          disabled={!file || pending}
          className="rounded bg-black px-4 py-2 text-white disabled:opacity-50"
        >
          {pending ? '분석 시작 중…' : '분석 시작'}
        </button>
      </div>
    </main>
  );
}