'use client';

import { useCallback, useRef, useState, useEffect } from "react";

/**
 * 기존 GAON 패턴을 따른 음성 녹음 컴포넌트
 * - 기존 FileDropzone과 동일한 구조 및 스타일링 방식 사용
 * - MediaRecorder API 기반 WebM 녹음
 * - 기존 UI 패턴 (버튼, 상태 표시) 활용
 */

type AudioRecorderProps = {
  onRecordingComplete: (audioBlob: Blob) => void; // 기존 페이지와 맞춤
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
  
  // 참조 (기존 패턴 따름)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

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

  // 녹음 시작 (기존 validate 함수 패턴 따름)
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 48000
        } 
      });
      
      streamRef.current = stream;
      
      // WebM 형식으로 녹음 (백엔드에서 지원하는 형식)
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
      };
      
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);
      
    } catch (error) {
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

  // 재녹음 (기존 패턴의 openPicker와 유사)
  const resetRecording = useCallback(() => {
    stopRecording();
    setAudioBlob(null);
    setRecordingTime(0);
  }, [stopRecording]);

  // 녹음 완료 및 전송
  const handleComplete = useCallback(() => {
    if (audioBlob) {
      onRecordingComplete(audioBlob);
    }
  }, [audioBlob, onRecordingComplete]);

  // 기존 FileDropzone 스타일 패턴 따름
  const containerClass = `
    relative border-2 border-dashed rounded-lg p-8 text-center transition-colors
    ${isRecording ? 'border-red-400 bg-red-50' : 'border-gray-300 bg-gray-50'}
    ${!isRecording && !audioBlob ? 'hover:border-gray-400 hover:bg-gray-100' : ''}
  `;

  return (
    <div className={containerClass}>
      {/* 녹음 상태 표시 */}
      {isRecording && (
        <div className="absolute top-2 right-2 flex items-center space-x-2">
          <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
          <span className="text-sm font-medium text-red-600">REC</span>
        </div>
      )}

      {/* 메인 컨텐츠 */}
      <div className="space-y-4">
        {/* 아이콘 및 상태 */}
        <div className="text-4xl">
          {isRecording ? '🎙️' : audioBlob ? '🎵' : '🎤'}
        </div>

        {/* 시간 표시 */}
        {(isRecording || audioBlob) && (
          <div className="text-2xl font-mono font-bold">
            {formatTime(recordingTime)}
          </div>
        )}

        {/* 상태별 메시지 */}
        <p className="text-gray-600">
          {isRecording 
            ? (isPaused ? '녹음이 일시정지되었습니다.' : '녹음 중입니다...')
            : audioBlob 
            ? '녹음이 완료되었습니다. 전송하거나 다시 녹음하세요.'
            : placeholder
          }
        </p>

        {/* 버튼 그룹 (기존 GAON 톤앤매너 적용) */}
        <div className="flex justify-center space-x-3">
          {!isRecording && !audioBlob && (
            <button
              onClick={startRecording}
              className="px-6 py-2 bg-black text-white rounded hover:bg-gray-800 transition-colors disabled:opacity-50"
            >
              녹음 시작
            </button>
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
    </div>
  );
}
