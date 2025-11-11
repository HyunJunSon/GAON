'use client';

import { useCallback, useRef, useState } from "react";

type AudioRecorderProps = {
  onRecordingComplete: (audioBlob: Blob) => void;
  onError?: (message: string) => void;
  maxDurationMinutes?: number;
};

export default function AudioRecorder({
  onRecordingComplete,
  onError,
  maxDurationMinutes = 10
}: AudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [duration, setDuration] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const startTimer = useCallback(() => {
    timerRef.current = setInterval(() => {
      setDuration(prev => {
        const newDuration = prev + 1;
        if (newDuration >= maxDurationMinutes * 60) {
          stopRecording();
          return prev;
        }
        return newDuration;
      });
    }, 1000);
  }, [maxDurationMinutes]);

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      chunksRef.current = [];
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start(1000);
      setIsRecording(true);
      setIsPaused(false);
      startTimer();
    } catch (error) {
      onError?.('마이크 접근 권한이 필요합니다.');
    }
  }, [onError, startTimer]);

  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.pause();
      setIsPaused(true);
      stopTimer();
    }
  }, [isRecording, stopTimer]);

  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current && isPaused) {
      mediaRecorderRef.current.resume();
      setIsPaused(false);
      startTimer();
    }
  }, [isPaused, startTimer]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsPaused(false);
      stopTimer();
    }
  }, [stopTimer]);

  const resetRecording = useCallback(() => {
    setDuration(0);
    setAudioBlob(null);
    chunksRef.current = [];
  }, []);

  const confirmRecording = useCallback(() => {
    if (audioBlob) {
      onRecordingComplete(audioBlob);
      resetRecording();
    }
  }, [audioBlob, onRecordingComplete, resetRecording]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="w-full space-y-4">
      {/* 녹음 상태 표시 */}
      <div className="rounded-lg border-2 border-dashed border-gray-300 bg-white p-6">
        <div className="flex flex-col items-center gap-4 text-center">
          {/* 녹음 시간 표시 */}
          <div className="text-2xl font-mono font-semibold text-gray-700">
            {formatTime(duration)}
          </div>
          
          {/* 상태 표시 */}
          <div className="text-sm text-gray-600">
            {isRecording && !isPaused && (
              <span className="flex items-center gap-2">
                <div className="h-2 w-2 animate-pulse rounded-full bg-red-500"></div>
                녹음 중...
              </span>
            )}
            {isPaused && (
              <span className="text-yellow-600">일시정지됨</span>
            )}
            {!isRecording && !audioBlob && (
              <span>녹음을 시작하려면 아래 버튼을 클릭하세요</span>
            )}
            {audioBlob && (
              <span className="text-green-600">녹음 완료</span>
            )}
          </div>

          {/* 제한 시간 안내 */}
          <div className="text-xs text-gray-500">
            최대 {maxDurationMinutes}분까지 녹음 가능
          </div>
        </div>
      </div>

      {/* 컨트롤 버튼들 */}
      <div className="flex justify-center gap-3">
        {!isRecording && !audioBlob && (
          <button
            type="button"
            onClick={startRecording}
            className="rounded bg-red-500 px-4 py-2 text-white hover:bg-red-600 transition"
          >
            🎙️ 녹음 시작
          </button>
        )}

        {isRecording && !isPaused && (
          <>
            <button
              type="button"
              onClick={pauseRecording}
              className="rounded bg-yellow-500 px-4 py-2 text-white hover:bg-yellow-600 transition"
            >
              ⏸️ 일시정지
            </button>
            <button
              type="button"
              onClick={stopRecording}
              className="rounded bg-gray-500 px-4 py-2 text-white hover:bg-gray-600 transition"
            >
              ⏹️ 중지
            </button>
          </>
        )}

        {isPaused && (
          <>
            <button
              type="button"
              onClick={resumeRecording}
              className="rounded bg-green-500 px-4 py-2 text-white hover:bg-green-600 transition"
            >
              ▶️ 재개
            </button>
            <button
              type="button"
              onClick={stopRecording}
              className="rounded bg-gray-500 px-4 py-2 text-white hover:bg-gray-600 transition"
            >
              ⏹️ 중지
            </button>
          </>
        )}

        {audioBlob && (
          <>
            <button
              type="button"
              onClick={resetRecording}
              className="rounded bg-gray-500 px-4 py-2 text-white hover:bg-gray-600 transition"
            >
              🔄 재녹음
            </button>
            <button
              type="button"
              onClick={confirmRecording}
              className="rounded bg-black px-4 py-2 text-white hover:bg-gray-800 transition"
            >
              ✅ 완료
            </button>
          </>
        )}
      </div>
    </div>
  );
}
