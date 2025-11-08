'use client';

import { useState } from 'react';
import { useStartAnalysis } from '@/hooks/useAnalysis';
import { useServerError } from '@/hooks/useServerError';
import ErrorAlert from '@/components/ui/ErrorAlert';
import FileDropzone from '@/components/upload/FileDropzone';
import { ChatRoom } from '@/components/realtime/ChatRoom';

// 텍스트 업로드 전용: 확장자/타입을 제한
const ACCEPT_MIME = ['text/plain'];
const ACCEPT_EXT = ['.txt']; // 필요 시 .md 등 추가
const MAX_MB = 5; // 텍스트는 작게 제한(필요 시 조정)

type TabType = 'upload' | 'realtime';

export default function ConversationPage() {
  const [activeTab, setActiveTab] = useState<TabType>('upload');
  const [file, setFile] = useState<File | null>(null);
  const { mutate, isPending } = useStartAnalysis();
  const { serverError, handleError, clearError } = useServerError();

  // 임시 사용자 정보 (실제로는 인증 컨텍스트에서 가져와야 함)
  const userId = 1;
  const familyId = 1;

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

  const handleSessionEnd = () => {
    // 세션 종료 후 처리 (예: 분석 페이지로 이동)
    console.log('실시간 대화 세션이 종료되었습니다.');
  };

  return (
    <main className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">대화 분석</h1>
        <p className="text-sm text-gray-600">
          파일을 업로드하거나 실시간으로 대화하여 분석을 시작합니다.
        </p>
      </header>

      {/* 탭 네비게이션 */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('upload')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'upload'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            파일 업로드
          </button>
          <button
            onClick={() => setActiveTab('realtime')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'realtime'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            실시간 대화
          </button>
        </nav>
      </div>

      {serverError && <ErrorAlert message={serverError} />}

      {/* 탭 콘텐츠 */}
      {activeTab === 'upload' && (
        <section className="space-y-6">
          <div className="space-y-3">
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
        </section>
      )}

      {activeTab === 'realtime' && (
        <section>
          <ChatRoom
            familyId={familyId}
            userId={userId}
            onSessionEnd={handleSessionEnd}
          />
        </section>
      )}
    </main>
  );
}