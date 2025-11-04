'use client';

import { useState } from 'react';
import { useStartAnalysis } from '@/hooks/useAnalysis';
import { useServerError } from '@/hooks/useServerError';
import ErrorAlert from '@/components/ui/ErrorAlert';
import FileDropzone from '@/components/upload/FileDropzone';

// 텍스트 업로드 전용: 확장자/타입을 제한
const ACCEPT_MIME = ['text/plain'];
const ACCEPT_EXT = ['.txt']; // 필요 시 .md 등 추가
const MAX_MB = 5; // 텍스트는 작게 제한(필요 시 조정)

export default function ConversationTextUploadPage() {
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
      { file, lang: 'ko' }, // 서버가 텍스트를 음성과 동일 엔드포인트에서 처리한다고 가정
      { onError: handleError }
    );
  };

  return (
    <main className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">텍스트 업로드</h1>
        <p className="text-sm text-gray-600">
          .txt 파일을 업로드하여 대화 분석을 시작합니다.
        </p>
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