'use client';

import { useState } from 'react';
import AudioRecorder from '@/components/upload/AudioRecorder';
import ErrorAlert from '@/components/ui/ErrorAlert';

export default function AudioConversationPage() {
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleRecordingComplete = (blob: Blob) => {
    setError(null);
    setAudioBlob(blob);
    console.log('녹음 완료:', blob.size, 'bytes');
  };

  const handleError = (message: string) => {
    setError(message);
  };

  const handleUpload = async () => {
    if (!audioBlob) return;

    setIsUploading(true);
    try {
      // TODO: 실제 API 호출 구현
      console.log('업로드 시작:', audioBlob);
      
      // 임시 지연
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      alert('업로드 완료! (임시)');
      setAudioBlob(null);
    } catch (err) {
      setError('업로드 중 오류가 발생했습니다.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <main className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">음성 대화 녹음</h1>
        <p className="text-sm text-gray-600">
          음성을 녹음하여 대화 분석을 시작합니다.
        </p>
      </header>

      {error && <ErrorAlert message={error} />}

      <section className="space-y-4">
        <AudioRecorder
          onRecordingComplete={handleRecordingComplete}
          onError={handleError}
          maxDurationMinutes={10}
        />

        {audioBlob && (
          <div className="rounded border bg-white px-4 py-3 text-sm text-gray-700">
            <div className="mb-2">
              <strong>녹음된 파일:</strong> {(audioBlob.size / 1024 / 1024).toFixed(2)} MB
            </div>
            <button
              type="button"
              onClick={handleUpload}
              disabled={isUploading}
              className="rounded bg-black px-4 py-2 text-white disabled:opacity-50 hover:bg-gray-800 transition"
            >
              {isUploading ? '업로드 중...' : '분석 시작'}
            </button>
          </div>
        )}
      </section>
    </main>
  );
}
