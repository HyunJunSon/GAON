'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import AudioRecorder from '@/components/upload/AudioRecorder';
import ErrorAlert from '@/components/ui/ErrorAlert';
import { uploadAudio, getConversationId } from '@/apis/analysis';

export default function AudioConversationPage() {
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleRecordingComplete = async (blob: Blob) => {
    setError(null);
    
    try {
      console.log('음성 업로드 시작:', blob.size, 'bytes');
      const result = await uploadAudio(blob);
      const conversationId = getConversationId(result);
      
      console.log('업로드 완료, conversationId:', conversationId);
      
      // 분석 페이지로 이동
      router.push(`/analysis/${conversationId}`);
      
    } catch (err) {
      console.error('업로드 실패:', err);
      setError(err instanceof Error ? err.message : '음성 업로드 중 오류가 발생했습니다.');
    }
  };

  const handleError = (message: string) => {
    setError(message);
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
      </section>
    </main>
  );
}
