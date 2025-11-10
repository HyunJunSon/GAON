'use client';
// 업로드/분석 요청 페이지 스켈레톤
// 지금은 실제 업로드/분석 요청 없이 UI 골격만 표시
// 2단계에서 FormData 업로드 + 서보 호출(POST /conversations/analyze) 연결 예정

import { useState } from 'react';
import { useStartAnalysis } from '@/hooks/useAnalysis';
import { useServerError } from '@/hooks/useServerError';
import ErrorAlert from '@/components/ui/ErrorAlert';
import FileDropzone from '@/components/upload/FileDropzone';

const ACCEPT_EXT = ['.mp3', '.wav', '.m4a'];
const ACCEPT_MIME = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav', 'audio/m4a']
const MAX_MB = 25;

export default function ConversationPage() {
  const [file, setFile] = useState<File | null>(null);
  const { mutate, isPending } = useStartAnalysis();
  const { serverError, handleError, clearError } = useServerError();

  const handleSelect = (files: File[]) => {
    clearError();
    setFile(files[0] ?? null);
  };

  const onStart = () => {
    if (!file) return;
    mutate(
      { file, lang: 'ko' },
      {
        onError: handleError
      }
    );
  };

  return (
    <main className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">대화 업로드</h1>
        <p className="text-sm text-gray-600">음성 파일을 선택하고 분석을 시작하세요.</p>
      </header>

      {serverError && <ErrorAlert message={serverError} />}

      <section className="space-y-3">
        <FileDropzone
          acceptExt={ACCEPT_EXT}
          acceptMime={ACCEPT_MIME}
          maxMB={MAX_MB}
          multiple={false}
          onFileSelect={handleSelect}
          onError={(msg) => handleError(new Error(msg))}
          placeholder="여기로 .txt 파일을 드래그하거나 클릭하여 선택하세요."
        />

        <div className="rounded border bg-white px-4 py-3 text-sm text-gray-700">
          {file
            ? <>선택된 파일: <strong>{file.name}</strong> ({(file.size / 1024 / 1024).toFixed(2)} MB)</>
            : '선택된 파일 없음'}
        </div>
      </section>
      <div>
        <button
          type="button"
          onClick={onStart}
          disabled={!file || isPending}
          className="rounded bg-black px-4 py-2 text-white disabled:opacity-50"
        >
          {isPending ? '분석 시작 중…' : '분석 시작'}
        </button>
      </div>
    </main>
  );
}