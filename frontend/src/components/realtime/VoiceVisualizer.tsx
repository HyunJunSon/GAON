import React, { useEffect, useRef } from 'react';

interface VoiceVisualizerProps {
  audioLevel: number;
  isRecording: boolean;
  isActive: boolean;
}

export const VoiceVisualizer: React.FC<VoiceVisualizerProps> = ({
  audioLevel,
  isRecording,
  isActive
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const draw = () => {
      const width = canvas.width;
      const height = canvas.height;
      
      // 캔버스 클리어
      ctx.clearRect(0, 0, width, height);

      if (isRecording || isActive) {
        // 중앙에서 시작하는 원형 파형
        const centerX = width / 2;
        const centerY = height / 2;
        const baseRadius = 30;
        const maxRadius = 60;
        
        // 음성 레벨에 따른 반지름 계산
        const radius = baseRadius + (audioLevel * (maxRadius - baseRadius));
        
        // 그라디언트 생성
        const gradient = ctx.createRadialGradient(
          centerX, centerY, 0,
          centerX, centerY, radius
        );
        
        if (isRecording) {
          gradient.addColorStop(0, 'rgba(255, 59, 48, 0.8)');
          gradient.addColorStop(1, 'rgba(255, 59, 48, 0.1)');
        } else {
          gradient.addColorStop(0, 'rgba(52, 199, 89, 0.8)');
          gradient.addColorStop(1, 'rgba(52, 199, 89, 0.1)');
        }

        // 메인 원 그리기
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
        ctx.fillStyle = gradient;
        ctx.fill();

        // 펄스 효과
        const time = Date.now() * 0.005;
        for (let i = 0; i < 3; i++) {
          const pulseRadius = radius + Math.sin(time + i * 0.5) * 10;
          ctx.beginPath();
          ctx.arc(centerX, centerY, pulseRadius, 0, 2 * Math.PI);
          ctx.strokeStyle = isRecording 
            ? `rgba(255, 59, 48, ${0.3 - i * 0.1})` 
            : `rgba(52, 199, 89, ${0.3 - i * 0.1})`;
          ctx.lineWidth = 2;
          ctx.stroke();
        }

        // 음성 바 표시 (상하좌우)
        const barCount = 8;
        const barLength = audioLevel * 20 + 5;
        
        for (let i = 0; i < barCount; i++) {
          const angle = (i / barCount) * 2 * Math.PI;
          const startX = centerX + Math.cos(angle) * (radius + 5);
          const startY = centerY + Math.sin(angle) * (radius + 5);
          const endX = centerX + Math.cos(angle) * (radius + 5 + barLength);
          const endY = centerY + Math.sin(angle) * (radius + 5 + barLength);
          
          ctx.beginPath();
          ctx.moveTo(startX, startY);
          ctx.lineTo(endX, endY);
          ctx.strokeStyle = isRecording 
            ? `rgba(255, 59, 48, ${0.8 - (i % 2) * 0.3})` 
            : `rgba(52, 199, 89, ${0.8 - (i % 2) * 0.3})`;
          ctx.lineWidth = 3;
          ctx.lineCap = 'round';
          ctx.stroke();
        }
      }

      animationRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [audioLevel, isRecording, isActive]);

  return (
    <div className="voice-visualizer">
      <canvas
        ref={canvasRef}
        width={150}
        height={150}
        className="visualizer-canvas"
      />
      {(isRecording || isActive) && (
        <div className="visualizer-label">
          {isRecording ? '🎤 녹음 중' : '🔊 음성 감지'}
        </div>
      )}
    </div>
  );
};
