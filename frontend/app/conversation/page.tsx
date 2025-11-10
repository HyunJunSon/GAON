'use client';

import { useState, useEffect } from 'react';
import { useStartAnalysis } from '@/hooks/useAnalysis';
import { useServerError } from '@/hooks/useServerError';
import ErrorAlert from '@/components/ui/ErrorAlert';
import FileDropzone from '@/components/upload/FileDropzone';
import { ChatRoom } from '@/components/realtime/ChatRoom';
import { ChatRoomList } from '@/components/realtime/ChatRoomList';
import { CreateChatRoom } from '@/components/realtime/CreateChatRoom';
import { apiFetch } from '@/apis/client';

// 다양한 문서 형식 지원
const ACCEPT_MIME = ['text/plain', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
const ACCEPT_EXT = ['.txt', '.pdf', '.docx'];
const MAX_MB = 10; // 문서 파일 크기 제한

type TabType = 'upload' | 'realtime';

export default function ConversationPage() {
  const [activeTab, setActiveTab] = useState<TabType>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [showCreateRoom, setShowCreateRoom] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [userInfo, setUserInfo] = useState<{userId: number, familyId: number} | null>(null);
  const { mutate, isPending } = useStartAnalysis();
  const { serverError, handleError, clearError } = useServerError();

  // 사용자 정보 가져오기
  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const userData = await apiFetch<{id: number, family_id: number}>('/api/auth/me');
        console.log('사용자 데이터:', userData); // 디버그 로그
        setUserInfo({
          userId: userData.id,
          familyId: userData.family_id || 1
        });
      } catch (error) {
        console.error('사용자 정보 조회 실패:', error);
        // 기본값 설정
        setUserInfo({ userId: 1, familyId: 1 });
      }
    };
    fetchUserInfo();
  }, []);

  if (!userInfo) {
    return <div className="flex justify-center items-center h-64">로딩 중...</div>;
  }

  const { userId, familyId } = userInfo;

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
            채팅
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
              placeholder="여기로 파일을 드래그하거나 클릭하여 선택하세요. (.txt, .pdf, .docx 지원)"
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
          <ChatRoomList
            familyId={familyId}
            userId={userId}
            onJoinRoom={(sessionId) => setActiveSessionId(sessionId)}
            onCreateRoom={() => setShowCreateRoom(true)}
            refreshTrigger={refreshTrigger}
          />
          
          {showCreateRoom && (
            <CreateChatRoom
              familyId={familyId}
              userId={userId}
              onRoomCreated={(sessionId) => {
                setActiveSessionId(sessionId);
                setShowCreateRoom(false);
                setRefreshTrigger(prev => prev + 1); // 목록 새로고침
              }}
              onCancel={() => setShowCreateRoom(false)}
            />
          )}
          
          {activeSessionId && userInfo && (
            <ChatRoom
              sessionId={activeSessionId}
              familyId={userInfo.familyId}
              userId={userInfo.userId}
              onSessionEnd={() => {
                setActiveSessionId(null);
                setRefreshTrigger(prev => prev + 1);
              }}
            />
          )}
        </section>
      )}
    </main>
  );
}