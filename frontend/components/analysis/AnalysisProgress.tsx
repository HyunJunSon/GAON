'use client';

import { useEffect, useState } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useNotificationStore } from '@/lib/notificationStore';

type AnalysisStep = 'cleaner' | 'analysis' | 'qa';

type ProgressData = {
  conversationId: string;
  currentStep: AnalysisStep;
  progress: number; // 0-100
  stepProgress: {
    cleaner: { status: 'pending' | 'running' | 'completed' | 'failed'; progress: number };
    analysis: { status: 'pending' | 'running' | 'completed' | 'failed'; progress: number };
    qa: { status: 'pending' | 'running' | 'completed' | 'failed'; progress: number };
  };
  estimatedTimeRemaining?: number; // 초
};

type AnalysisProgressProps = {
  conversationId: string;
  onComplete?: () => void;
  onError?: (error: string) => void;
};

export default function AnalysisProgress({ 
  conversationId, 
  onComplete, 
  onError 
}: AnalysisProgressProps) {
  const [progressData, setProgressData] = useState<ProgressData | null>(null);
  const { addNotification } = useNotificationStore();

  const { isConnected } = useWebSocket({
    conversationId,
    onAnalysisComplete: (data) => {
      setProgressData(data);
      addNotification({
        type: 'success',
        title: '분석 완료!',
        message: '대화 분석이 성공적으로 완료되었습니다.',
        conversationId,
        link: `/analysis/${conversationId}/summary`
      });
      onComplete?.();
    },
    onAnalysisProgress: (data) => {
      setProgressData(data);
    },
    onAnalysisError: (error) => {
      addNotification({
        type: 'error',
        title: '분석 실패',
        message: error || '분석 중 오류가 발생했습니다.',
        conversationId
      });
      onError?.(error);
    }
  });

  const getStepLabel = (step: AnalysisStep) => {
    switch (step) {
      case 'cleaner': return '데이터 정제';
      case 'analysis': return '대화 분석';
      case 'qa': return '품질 검증';
    }
  };

  const getStepIcon = (step: AnalysisStep, status: string) => {
    if (status === 'completed') return '✅';
    if (status === 'failed') return '❌';
    if (status === 'running') return '⚙️';
    return '⏳';
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}분 ${secs}초`;
  };

  if (!progressData) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-gray-300 border-t-black rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-sm text-gray-600">분석 준비 중...</p>
          {!isConnected && (
            <p className="text-xs text-red-500 mt-2">연결 중...</p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">분석 진행 상황</h3>
        <div className="text-sm text-gray-500">
          {progressData.progress}% 완료
        </div>
      </div>

      {/* 전체 진행률 */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">전체 진행률</span>
          {progressData.estimatedTimeRemaining && (
            <span className="text-xs text-gray-500">
              예상 완료: {formatTime(progressData.estimatedTimeRemaining)}
            </span>
          )}
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-black h-2 rounded-full transition-all duration-300"
            style={{ width: `${progressData.progress}%` }}
          ></div>
        </div>
      </div>

      {/* 단계별 진행률 */}
      <div className="space-y-4">
        {(['cleaner', 'analysis', 'qa'] as AnalysisStep[]).map((step) => {
          const stepData = progressData.stepProgress[step];
          const isActive = progressData.currentStep === step;
          
          return (
            <div 
              key={step}
              className={`flex items-center space-x-4 p-3 rounded-lg transition-colors ${
                isActive ? 'bg-blue-50 border border-blue-200' : 'bg-gray-50'
              }`}
            >
              
              {/* 아이콘 */}
              <div className="text-lg">
                {getStepIcon(step, stepData.status)}
              </div>
              
              {/* 단계 정보 */}
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-sm font-medium ${
                    isActive ? 'text-blue-900' : 'text-gray-700'
                  }`}>
                    {getStepLabel(step)}
                  </span>
                  <span className="text-xs text-gray-500">
                    {stepData.progress}%
                  </span>
                </div>
                
                {/* 단계별 진행률 바 */}
                <div className="w-full bg-gray-200 rounded-full h-1">
                  <div 
                    className={`h-1 rounded-full transition-all duration-300 ${
                      stepData.status === 'completed' ? 'bg-green-500' :
                      stepData.status === 'failed' ? 'bg-red-500' :
                      stepData.status === 'running' ? 'bg-blue-500' : 'bg-gray-300'
                    }`}
                    style={{ width: `${stepData.progress}%` }}
                  ></div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* 연결 상태 */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>실시간 업데이트</span>
          <span className={`flex items-center space-x-1 ${
            isConnected ? 'text-green-600' : 'text-red-600'
          }`}>
            <div className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}></div>
            <span>{isConnected ? '연결됨' : '연결 끊김'}</span>
          </span>
        </div>
      </div>
    </div>
  );
}
