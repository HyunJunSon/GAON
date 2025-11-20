'use client';

import { useState } from 'react';
import { useServerError } from '@/hooks/useServerError';
import { useGlobalNotification } from '@/hooks/useGlobalNotification';
import { useGlobalWebSocket } from '@/hooks/useGlobalWebSocket';
import { analysisHistoryStorage } from '@/utils/analysisHistoryStorage';
import ErrorAlert from '@/components/ui/ErrorAlert';
import AudioRecorder from '@/components/upload/AudioRecorder';
import SpeakerMappingModal from '@/components/upload/SpeakerMappingModal';
import { uploadAudio, getConversationId } from '@/apis/analysis';
import { useRouter } from 'next/navigation';

export default function ConversationPage() {
  const [showSpeakerModal, setShowSpeakerModal] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [modalStatus, setModalStatus] = useState<'uploading' | 'processing' | 'ready'>('uploading');
  const { serverError, handleError, clearError } = useServerError();
  const { showNotification } = useGlobalNotification();
  useGlobalWebSocket(currentConversationId || undefined); // WebSocket 연결
  const router = useRouter();

  const handleRecordingComplete = async (blob: Blob) => {
    clearError();
    
    try {
      console.log('음성 업로드 시작:', blob.size, 'bytes');
      
      // 모달 표시 및 업로드 상태
      setModalStatus('uploading');
      setShowSpeakerModal(true);
      
      const result = await uploadAudio(blob);
      const conversationId = getConversationId(result);
      setCurrentConversationId(conversationId);
      
      console.log('업로드 완료, conversationId:', conversationId);
      
      // STT 처리 중 상태로 변경
      setModalStatus('processing');
      
      // STT 완료 대기 (실제로는 폴링이나 웹소켓으로 상태 확인)
      setTimeout(() => {
        setModalStatus('ready');
      }, 3000); // 임시로 3초 후 ready 상태
      
    } catch (err) {
      console.error('업로드 실패:', err);
      handleError(err instanceof Error ? err : new Error('음성 업로드 중 오류가 발생했습니다.'));
      setShowSpeakerModal(false);
    }
  };

  const handleSpeakerMappingComplete = (mapping: Record<string, string>) => {
    console.log('화자 맵핑 완료:', mapping);
    
    // 분석 히스토리에 저장
    if (currentConversationId) {
      analysisHistoryStorage.save({
        conversationId: currentConversationId,
        title: `대화 분석 ${new Date().toLocaleDateString('ko-KR')}`,
        createdAt: new Date().toISOString(),
        status: 'processing'
      });
    }
    
    // 화자 매핑 완료 후 모달 닫고 홈으로 돌아가기
    setShowSpeakerModal(false);
    setCurrentConversationId(null);
    setModalStatus('uploading');
    
    // 사용자에게 알림 표시
    showNotification({
      title: '화자 설정 완료!',
      body: '분석이 백그라운드에서 진행됩니다. 완료되면 알려드릴게요.',
      onClick: () => {
        if (currentConversationId) {
          router.push(`/analysis/${currentConversationId}/summary`);
        }
      }
    });
  };

  const handleModalClose = () => {
    setShowSpeakerModal(false);
    setCurrentConversationId(null);
    setModalStatus('uploading');
  };

  return (
    <main className="mx-auto w-full max-w-5xl space-y-8 px-4 pb-16 pt-8 md:space-y-10 md:px-0">
      {/* 헤더 섹션 - 브랜드 디자인 적용 */}
      <header className="rounded-3xl border border-orange-200 bg-gradient-to-br from-orange-50 via-white to-red-100 p-8 shadow-inner">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-500 to-red-500 text-white shadow-lg">
                <svg className="h-7 w-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide text-orange-600">Conversation Upload</p>
                <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">대화 분석 시작</h1>
              </div>
            </div>
            <p className="text-base leading-relaxed text-gray-600 md:text-lg">
              음성 녹음으로 대화를 업로드하고 AI 분석을 통해 관계의 온도를 측정해보세요. 
              실시간 녹음과 화자 설정을 통해 정확한 분석 결과를 얻을 수 있습니다.
            </p>
          </div>
          <div className="rounded-2xl border border-white/80 bg-white/70 px-6 py-5 shadow-lg backdrop-blur">
            <p className="text-sm font-medium text-gray-500">지원 형식</p>
            <div className="mt-3 space-y-2 text-sm text-gray-700">
              <p className="font-semibold text-orange-600">음성 녹음</p>
              <p className="text-xs text-gray-500">최대 10분까지 녹음 가능</p>
            </div>
          </div>
        </div>
      </header>

      {/* 음성 녹음 섹션 */}
      <section className="rounded-2xl border border-orange-100 bg-white p-8 shadow-lg">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500/20 to-red-500/20 flex items-center justify-center text-orange-600">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">음성 녹음</h2>
            <p className="text-sm text-gray-500">실시간 음성 녹음으로 대화 분석을 시작합니다.</p>
          </div>
        </div>

        {serverError && (
          <div className="mb-6">
            <ErrorAlert message={serverError} />
          </div>
        )}

        <div className="max-w-2xl mx-auto">
          <AudioRecorder
            onRecordingComplete={handleRecordingComplete}
            onError={handleError}
            maxDurationMinutes={10}
          />
        </div>
      </section>
      
      {/* 화자 맵핑 모달 */}
      <SpeakerMappingModal
        conversationId={currentConversationId || ''}
        isOpen={showSpeakerModal}
        onClose={handleModalClose}
        onComplete={handleSpeakerMappingComplete}
        status={modalStatus}
      />
    </main>
  );
}
