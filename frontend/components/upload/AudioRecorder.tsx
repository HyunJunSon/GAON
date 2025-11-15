'use client';

import { useCallback, useRef, useState, useEffect } from "react";

/**
 * 기존 GAON 패턴을 따른 음성 녹음 컴포넌트
 * - 기존 FileDropzone과 동일한 구조 및 스타일링 방식 사용
 * - MediaRecorder API 기반 WebM 녹음
 * - 실시간 Canvas 파형 시각화 (GAON 디자인 시스템 적용)
 * - 기존 UI 패턴 (버튼, 상태 표시) 활용
 */

type AudioRecorderProps = {
  onRecordingComplete: (audioBlob: Blob) => void;
  onError?: (message: string) => void;
  maxDurationMinutes?: number; // 최대 녹음 시간 (분)
  placeholder?: string;
};

export default function AudioRecorder({
  onRecordingComplete,
  onError,
  maxDurationMinutes = 10,
  placeholder = '음성 녹음을 시작하려면 버튼을 클릭하세요.'
}: AudioRecorderProps) {
  // 상태 관리 (기존 FileDropzone 패턴 따름)
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  
  // 참조 (기존 패턴 따름)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const animationRef = useRef<number | null>(null);
  const waveformRef = useRef<HTMLDivElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // 타이머 업데이트
  useEffect(() => {
    if (isRecording && !isPaused) {
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => {
          const newTime = prev + 1;
          // 최대 시간 초과 시 자동 중지
          if (newTime >= maxDurationMinutes * 60) {
            stopRecording();
          }
          return newTime;
        });
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isRecording, isPaused, maxDurationMinutes]);

  // 시간 포맷팅 (MM:SS)
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // 녹음 시작
  const startRecording = useCallback(async () => {
    console.log('🎙️ 녹음 시작 버튼 클릭됨');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false
        } 
      });
      console.log('✅ 마이크 접근 성공');
      
      streamRef.current = stream;
      
      // WebM 형식으로 녹음
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      const chunks: BlobPart[] = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        setAudioBlob(blob);
        console.log('🎵 녹음 완료:', blob.size, 'bytes');
      };
      
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);
      
    } catch (error) {
      console.error('❌ 녹음 시작 실패:', error);
      onError?.('마이크 접근 권한이 필요합니다. 브라우저 설정을 확인해주세요.');
    }
  }, [onError]);

  // 녹음 중지
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsPaused(false);
      
      // 스트림 정리
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
    }
  }, [isRecording]);

  // 녹음 일시정지/재개
  const togglePause = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      if (isPaused) {
        mediaRecorderRef.current.resume();
        setIsPaused(false);
      } else {
        mediaRecorderRef.current.pause();
        setIsPaused(true);
      }
    }
  }, [isRecording, isPaused]);

  // 재녹음
  const resetRecording = useCallback(() => {
    stopRecording();
    setAudioBlob(null);
    setUploadedFile(null);
    setRecordingTime(0);
    
    // 실시간 파형 애니메이션 중지
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
    
    // Canvas 정리
    if (waveformRef.current) {
      const canvas = waveformRef.current.querySelector('canvas');
      if (canvas) {
        canvas.remove();
      }
    }
  }, [stopRecording]);

  // 파일 업로드 핸들러 (GAON 스타일 + STT 최적화)
  const handleFileUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // 지원하는 오디오 형식 검증 (백엔드 STT 서비스 기준)
    const supportedFormats = ['audio/mp3', 'audio/mpeg', 'audio/wav', 'audio/webm', 'audio/mp4', 'audio/x-m4a'];
    const fileExtension = file.name.toLowerCase().split('.').pop();
    const supportedExtensions = ['mp3', 'wav', 'webm', 'm4a'];

    if (!supportedFormats.includes(file.type) && !supportedExtensions.includes(fileExtension || '')) {
      onError?.('지원하는 오디오 형식: MP3, WAV, WebM, M4A');
      return;
    }

    // 파일 크기 제한 (50MB - Google STT 제한)
    if (file.size > 50 * 1024 * 1024) {
      onError?.('파일 크기는 50MB 이하여야 합니다.');
      return;
    }

    setUploadedFile(file);
    setAudioBlob(file);
    
    // 오디오 파일의 재생 시간 계산
    const audio = new Audio();
    audio.onloadedmetadata = () => {
      setRecordingTime(Math.floor(audio.duration));
    };
    audio.onerror = () => {
      onError?.('오디오 파일을 읽을 수 없습니다.');
    };
    audio.src = URL.createObjectURL(file);
    
    console.log('📁 파일 업로드 완료:', file.name, file.size, 'bytes');
  }, [onError]);

  // 파일 선택 버튼 클릭
  const handleFileSelect = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  // 녹음 완료 확인 다이얼로그 표시
  const handleComplete = useCallback(() => {
    setShowConfirmDialog(true);
  }, []);

  // 최종 전송 확인
  const handleConfirmSubmit = useCallback(async () => {
    if (audioBlob) {
      setIsProcessing(true);
      try {
        await onRecordingComplete(audioBlob);
        setShowConfirmDialog(false);
        // 성공 후 상태 초기화
        setAudioBlob(null);
        setRecordingTime(0);
      } catch (error) {
        onError?.('음성 파일 전송에 실패했습니다. 다시 시도해주세요.');
      } finally {
        setIsProcessing(false);
      }
    }
  }, [audioBlob, onRecordingComplete, onError]);

  // 전송 취소
  const handleCancelSubmit = useCallback(() => {
    setShowConfirmDialog(false);
  }, []);

  // 기존 FileDropzone 스타일 패턴 따름
  const containerClass = `
    relative border-2 border-dashed rounded p-8 text-center transition-colors
    ${isRecording ? 'border-gray-400 bg-gray-50' : 'border-gray-300 bg-gray-50'}
    ${!isRecording && !audioBlob ? 'hover:border-gray-400 hover:bg-gray-100' : ''}
  `;

  return (
    <div className={containerClass}>
      {/* 녹음 상태 표시 */}
      {isRecording && (
        <div className="absolute top-2 right-2 flex items-center space-x-2">
          <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
          <span className="text-sm font-medium text-red-500">REC</span>
        </div>
      )}

      {/* 메인 컨텐츠 */}
      <div className="space-y-4">
        {/* 아이콘 및 상태 */}
        <div className="text-4xl">
          {isRecording ? '🎙️' : audioBlob ? '🎵' : '🎤'}
        </div>

        {/* 녹음 시각화 영역 - CSS 애니메이션 원형 파동 */}
        <div className="mx-auto max-w-md">
          <div className={`
            flex items-center justify-center transition-opacity
            ${isRecording || audioBlob ? 'opacity-100' : 'opacity-30'}
          `} style={{ minHeight: '120px' }}>
            {isRecording ? (
              <div className="relative flex items-center justify-center">
                {/* 중앙 마이크 아이콘 */}
                <div className="w-12 h-12 bg-black rounded-full flex items-center justify-center text-white text-xl z-10">
                  🎙️
                </div>
                {/* 파동 효과 */}
                <div className="absolute w-16 h-16 border-2 border-black rounded-full animate-ping opacity-75"></div>
                <div className="absolute w-24 h-24 border-2 border-gray-400 rounded-full animate-ping opacity-50" style={{animationDelay: '0.5s'}}></div>
                <div className="absolute w-32 h-32 border-2 border-gray-300 rounded-full animate-ping opacity-25" style={{animationDelay: '1s'}}></div>
              </div>
            ) : audioBlob ? (
              <div className="flex items-center space-x-2 text-black">
                <span className="text-2xl">🎵</span>
                <span className="font-medium">녹음 완료 ({formatTime(recordingTime)})</span>
              </div>
            ) : (
              <div className="text-gray-400 text-sm text-center">
                <div className="text-4xl mb-2">🎤</div>
                <div>음성 녹음 준비</div>
              </div>
            )}
          </div>
        </div>

        {/* 시간 표시 */}
        {(isRecording || audioBlob) && (
          <div className="text-2xl font-mono font-bold text-black">
            {formatTime(recordingTime)}
          </div>
        )}

        {/* 상태별 메시지 */}
        <p className="text-gray-600">
          {isRecording 
            ? (isPaused ? '녹음이 일시정지되었습니다.' : '녹음 중입니다...')
            : audioBlob 
            ? (uploadedFile ? `음성이 업로드되었습니다: ${uploadedFile.name}` : '녹음이 완료되었습니다. 파형을 확인하고 전송하거나 다시 녹음하세요.')
            : placeholder
          }
        </p>

        {/* 버튼 그룹 */}
        <div className="flex justify-center space-x-3">
          {!isRecording && !audioBlob && (
            <>
              <button
                onClick={() => {
                  console.log('🔴 녹음 시작 버튼 클릭됨!');
                  startRecording();
                }}
                className="px-6 py-2 bg-black text-white rounded hover:bg-gray-800 transition-colors disabled:opacity-50"
              >
                녹음 시작
              </button>
              <button
                onClick={handleFileSelect}
                className="px-6 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
              >
                음성 업로드
              </button>
            </>
          )}

          {isRecording && (
            <>
              <button
                onClick={togglePause}
                className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
              >
                {isPaused ? '재개' : '일시정지'}
              </button>
              <button
                onClick={stopRecording}
                className="px-4 py-2 bg-black text-white rounded hover:bg-gray-800 transition-colors"
              >
                중지
              </button>
            </>
          )}

          {audioBlob && (
            <>
              <button
                onClick={handleComplete}
                className="px-6 py-2 bg-black text-white rounded hover:bg-gray-800 transition-colors"
              >
                완료
              </button>
              <button
                onClick={resetRecording}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
              >
                다시 녹음
              </button>
            </>
          )}
        </div>

        {/* 진행률 표시 */}
        {isRecording && (
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-black h-2 rounded-full transition-all duration-1000"
              style={{ width: `${(recordingTime / (maxDurationMinutes * 60)) * 100}%` }}
            ></div>
          </div>
        )}
      </div>

      {/* 확인 다이얼로그 - 기존 GAON 패턴 */}
      {showConfirmDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded p-6 max-w-sm w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">
              {uploadedFile ? '음성 업로드 완료' : '음성 녹음 완료'}
            </h3>
            <p className="text-gray-600 mb-6">
              {uploadedFile ? '업로드된 파일을' : '녹음된 음성을'} 전송하시겠습니까?<br/>
              <span className="text-sm text-gray-500">
                {uploadedFile ? `파일명: ${uploadedFile.name}` : `녹음 시간: ${formatTime(recordingTime)}`}
              </span>
            </p>
            <div className="flex space-x-3">
              <button
                onClick={handleCancelSubmit}
                disabled={isProcessing}
                className="flex-1 px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors disabled:opacity-50"
              >
                취소
              </button>
              <button
                onClick={handleConfirmSubmit}
                disabled={isProcessing}
                className="flex-1 px-4 py-2 bg-black text-white rounded hover:bg-gray-800 transition-colors disabled:opacity-50"
              >
                {isProcessing ? '전송 중...' : '전송'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 숨겨진 파일 입력 */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".mp3,.wav,.webm,.m4a,audio/mp3,audio/mpeg,audio/wav,audio/webm,audio/mp4,audio/x-m4a"
        onChange={handleFileUpload}
        className="hidden"
      />
    </div>
  );
}
