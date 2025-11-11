'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useStartAnalysis } from '@/hooks/useAnalysis';
import { useServerError } from '@/hooks/useServerError';
import ErrorAlert from '@/components/ui/ErrorAlert';
import FileDropzone from '@/components/upload/FileDropzone';
import AudioRecorder from '@/components/upload/AudioRecorder';
import { uploadAudio, getConversationId } from '@/apis/analysis';
import { useRouter } from 'next/navigation';

// 텍스트 업로드 전용: 확장자/타입을 제한
const ACCEPT_MIME = ['text/plain'];
const ACCEPT_EXT = ['.txt'];
const MAX_MB = 5;

export default function ConversationPage() {
  const [activeTab, setActiveTab] = useState<'text' | 'audio'>('text');
  const [file, setFile] = useState<File | null>(null);
  const { mutate, isPending } = useStartAnalysis();
  const { serverError, handleError, clearError } = useServerError();
  const router = useRouter();

  const handleSelect = (files: File[]) => {
    clearError();
    setFile(files[0] ?? null);
  };

  const onStart = () => {
    if (!file) return;
    mutate(
      { file, lang: 'ko' },
      { onError: handleError }
    );
  };

  const handleRecordingComplete = async (blob: Blob) => {
    clearError();
    
    try {
      console.log('음성 업로드 시작:', blob.size, 'bytes');
      const result = await uploadAudio(blob);
      const conversationId = getConversationId(result);
      
      console.log('업로드 완료, conversationId:', conversationId);
      router.push(`/analysis/${conversationId}/summary`);
      
    } catch (err) {
      console.error('업로드 실패:', err);
      handleError(err instanceof Error ? err : new Error('음성 업로드 중 오류가 발생했습니다.'));
    }
  };

  return (
    <main className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">대화 분석</h1>
        <p className="text-sm text-gray-600">
          텍스트 파일 또는 음성 녹음으로 대화 분석을 시작합니다.
        </p>
      </header>

      {/* 탭 네비게이션 */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('text')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'text'
                ? 'border-black text-black'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            📄 텍스트 업로드
          </button>
          <button
            onClick={() => setActiveTab('audio')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'audio'
                ? 'border-black text-black'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            🎙️ 음성 녹음
          </button>
        </nav>
      </div>

      {serverError && <ErrorAlert message={serverError} />}

      {/* 탭 컨텐츠 */}
      {activeTab === 'text' && (
        <section className="space-y-4">
          <div className="max-w-2xl">
            <h2 className="text-lg font-medium mb-2">텍스트 파일 업로드</h2>
            <p className="text-sm text-gray-600 mb-4">
              .txt 파일을 업로드하여 대화 분석을 시작합니다.
            </p>

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
          </div>
          
          <div className='flex justify-center'>
            <button
              type="button"
              onClick={onStart}
              disabled={!file || isPending}
              className="rounded bg-black w-full max-w-80 px-4 py-2 text-white disabled:opacity-50"
            >
              {isPending ? '분석 시작 중…' : '분석 시작'}
            </button>
          </div>
        </section>
      )}

      {activeTab === 'audio' && (
        <section className="space-y-4">
          <div className="max-w-2xl">
            <h2 className="text-lg font-medium mb-2">음성 녹음</h2>
            <p className="text-sm text-gray-600 mb-4">
              실시간 음성 녹음으로 대화 분석을 시작합니다.
            </p>

            <AudioRecorder
              onRecordingComplete={handleRecordingComplete}
              onError={handleError}
              maxDurationMinutes={10}
            />
          </div>
        </section>
      )}
    </main>
  );
}
