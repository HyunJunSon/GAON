'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useStartAnalysis } from '@/hooks/useAnalysis';
import { useServerError } from '@/hooks/useServerError';
import { useGlobalNotification } from '@/hooks/useGlobalNotification';
import { useGlobalWebSocket } from '@/hooks/useGlobalWebSocket';
import { analysisHistoryStorage } from '@/utils/analysisHistoryStorage';
import ErrorAlert from '@/components/ui/ErrorAlert';
import FileDropzone from '@/components/upload/FileDropzone';
import AudioRecorder from '@/components/upload/AudioRecorder';
import SpeakerMappingModal from '@/components/upload/SpeakerMappingModal';
import { uploadAudio, getConversationId } from '@/apis/analysis';
import { useRouter } from 'next/navigation';

// 백엔드와 동기화된 파일 타입 설정
const ACCEPT_MIME = [
  'text/plain',
  'application/pdf', 
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/epub+zip',
  'text/markdown'
];
const ACCEPT_EXT = ['.txt', '.pdf', '.docx', '.epub', '.md'];
const MAX_MB = 10; // 백엔드 설정과 동일

export default function ConversationPage() {
  const [activeTab, setActiveTab] = useState<'text' | 'audio'>('text');
  const [file, setFile] = useState<File | null>(null);
  const [showSpeakerModal, setShowSpeakerModal] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [modalStatus, setModalStatus] = useState<'uploading' | 'processing' | 'ready'>('uploading');
  const { mutate, isPending } = useStartAnalysis();
  const { serverError, handleError, clearError } = useServerError();
  const { showNotification } = useGlobalNotification();
  useGlobalWebSocket(currentConversationId || undefined); // WebSocket 연결
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
    <main className="space-y-8">
      {/* 헤더 섹션 */}
      <header className="text-center">
        <div className="inline-flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-gradient-to-br from-orange-100 to-red-100 rounded-xl flex items-center justify-center">
            <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-800">대화 분석</h1>
        </div>
        <p className="text-gray-600 text-lg max-w-2xl mx-auto">
          다양한 형식의 파일 또는 음성 녹음으로 대화 분석을 시작하여<br />
          관계의 온도를 측정해보세요
        </p>
      </header>

      {/* 탭 네비게이션 */}
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl shadow-lg border border-orange-100 overflow-hidden">
          <nav className="flex">
            <button
              onClick={() => setActiveTab('text')}
              className={`flex-1 py-4 px-6 font-medium text-center transition-all duration-200 ${
                activeTab === 'text'
                  ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white'
                  : 'text-gray-600 hover:text-orange-600 hover:bg-orange-50'
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                파일 업로드
              </div>
            </button>
            <button
              onClick={() => setActiveTab('audio')}
              className={`flex-1 py-4 px-6 font-medium text-center transition-all duration-200 ${
                activeTab === 'audio'
                  ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white'
                  : 'text-gray-600 hover:text-orange-600 hover:bg-orange-50'
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
                음성 녹음
              </div>
            </button>
          </nav>

          {serverError && (
            <div className="p-6 border-t border-orange-100">
              <ErrorAlert message={serverError} />
            </div>
          )}

          {/* 탭 컨텐츠 */}
          <div className="p-8">
            {activeTab === 'text' && (
              <section className="space-y-6">
                <div className="text-center">
                  <h2 className="text-xl font-semibold text-gray-800 mb-2">대화 파일 업로드</h2>
                  <p className="text-gray-600">
                    텍스트 파일(.txt, .md), 문서 파일(.pdf, .docx, .epub)을 업로드하여 대화 분석을 시작합니다.
                  </p>
                </div>

                <div className="max-w-2xl mx-auto space-y-6">
                  <FileDropzone
                    acceptExt={ACCEPT_EXT}
                    acceptMime={ACCEPT_MIME}
                    maxMB={MAX_MB}
                    multiple={false}
                    onFileSelect={handleSelect}
                    onError={(msg) => handleError(new Error(msg))}
                    placeholder="여기로 파일을 드래그하거나 클릭하여 선택하세요"
                  />

                  <div className="bg-orange-50 border border-orange-200 rounded-lg px-4 py-3 text-center">
                    {file ? (
                      <div className="text-gray-700">
                        <span className="font-medium text-orange-700">선택된 파일:</span> {file.name}
                        <span className="text-sm text-gray-500 ml-2">
                          ({(file.size / 1024 / 1024).toFixed(2)} MB)
                        </span>
                      </div>
                    ) : (
                      <span className="text-gray-500">선택된 파일 없음</span>
                    )}
                  </div>

                  <div className="text-center">
                    <button
                      type="button"
                      onClick={onStart}
                      disabled={!file || isPending}
                      className="bg-gradient-to-r from-orange-500 to-red-500 text-white px-8 py-3 rounded-lg font-medium hover:from-orange-600 hover:to-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-md hover:shadow-lg"
                    >
                      {isPending ? '분석 시작 중…' : '분석 시작'}
                    </button>
                  </div>
                </div>
              </section>
            )}

            {activeTab === 'audio' && (
              <section className="space-y-6">
                <div className="text-center">
                  <h2 className="text-xl font-semibold text-gray-800 mb-2">음성 녹음</h2>
                  <p className="text-gray-600">
                    실시간 음성 녹음으로 대화 분석을 시작합니다.
                  </p>
                </div>

                <div className="max-w-2xl mx-auto">
                  <AudioRecorder
                    onRecordingComplete={handleRecordingComplete}
                    onError={handleError}
                    maxDurationMinutes={10}
                  />
                </div>
              </section>
            )}
          </div>
        </div>
      </div>
      
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
