'use client';

import { useCallback, useRef, useState } from "react";

/**
 * 접근성 지원 + 드래그앤드롭(DnD) + 클릭 선택 지원 드롭존
 * - 외부 상태로 파일을 올려보내기 위해 onFileSelect 콜백 사용
 * - accept : 확장자 or MIME 배열(브라우저가 MIME을 비울 수 있으므로 확장자 검사도 병행)
 */
// 1. 인터페이스(Props)와 기본값 정하기
// 1.1. 컴포넌트가 받아야 할 입력 규격을 정의
type FileDropzoneProps = {
  acceptExt?: string[]; // ['.txt'] 같은 확장자
  acceptMime?: string[]; // ['text/plain'] 같은 MIME
  maxMB?: number; // 허용 용량 (MB)
  multiple?: boolean; // 다중 파일 허용 여부(기본 false)
  onFileSelect: (files: File[]) => void; // 유효성 통과 파일 전달
  onError?: (message: string) => void; // 유효성 실패 메시지 전달
  placeholder?: string; // 안내 문구
};

// 1.2. 매개변수 기본값을 지정해서 아무 값도 안줘도 작동하도록 함
export default function FileDropzone({
  acceptExt = ['.txt', '.pdf', '.docx'], // 백엔드와 동기화
  acceptMime = ['text/plain', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'], // 백엔드와 동기화
  maxMB = 50, // 백엔드와 동기화 (50MB)
  multiple = false,
  onFileSelect,
  onError,
  placeholder = '여기로 파일을 드래그하거나 클릭하여 선택하세요.'
}: FileDropzoneProps) {
  // 2. 내부 상태/참조 준비
  const inputRef = useRef<HTMLInputElement | null>(null); // input 요소 제어를 위한 inputRef
  const [isDragging, setIsDragging] = useState(false); // 드래그 중임을 표시
  const [hovered, setHovered] = useState(false); // 마우스 오버 표시

  // 3. 보조 함수 : 파일 선택창 열기
  // openPicker를 통해서 숨겨진 input 요소 클릭
  const openPicker = () => inputRef.current?.click();

  // 4. 유효성 검사
  // useCallback으로 해당 함수가 모든 진입점(드래그/클릭)에서 공통으로 호출
  const validate = useCallback(
    (files: File[]) => {
      if (!files.length) return;
      const errors: string[] = [];
      const valid: File[] = [];
      for (const f of files) {
        const sizeOk = f.size <= maxMB * 1024 * 1024;
        // 확장자 검사(소문자화)
        const lowerName = f.name.toLowerCase();
        const extOk = acceptExt.length === 0 || acceptExt.some((ext) => lowerName.endsWith(ext));
        // MIME 검사(일부 브라우저는 빈 문자열일 수 있음 → 확장자와 OR 로직)
        const mimeOk =
          !f.type || acceptMime.length === 0 || acceptMime.includes(f.type);

        if (!sizeOk) {
          errors.push(`"${f.name}" 용량 초과 (최대 ${maxMB}MB)`);
          continue;
        }
        if (!extOk && !mimeOk) {
          errors.push(`"${f.name}" 형식 미지원 (${acceptExt.join(', ')})`);
          continue;
        }
        valid.push(f);
        if (!multiple) break; // 단일 모드면 첫 유효 파일만
      }
      if (errors.length) onError?.(errors.join('\n'));
      if (valid.length) onFileSelect(valid);
    },
    [acceptExt, acceptMime, maxMB, multiple, onError, onFileSelect]
  )

  // 5. 입력 경로1 : 파일 입력창
  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    validate(files);
    // 같은 파일 다시 선택해도 change 이벤트 발생하도록 reset
    e.target.value = '';
  }
  // 6. 입력 경로2 : 드래그앤드롭
  const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
    // 기본 동작/전파 방지
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    // 파일 추출 후 validate 호출
    const dt = e.dataTransfer;
    const files = Array.from(dt.files ?? []);
    validate(files);
  }
  const onDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    // 기본 동작(브라우저가 파일을 열어버리는 것 등) 막기
    e.preventDefault();
    e.stopPropagation();
    if (!isDragging) setIsDragging(true);
  }
  const onDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    // 영역 밖으로 완전히 나갔을 때만 drag 상태 해제
    // 버블링 때문에 if (e.currentTarget === e.target) 조건으로 깜빡임 방지
    if (e.currentTarget === e.target) setIsDragging(false);
  }

  return (
    <div className="w-full">
      <div
        role="button"
        tabIndex={0}
        aria-label="파일 업로드 영역"
        onClick={openPicker}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        className={[
          'rounded-lg border-2 border-dashed p-6 transition',
          'bg-white', hovered ? 'border-gray-400 cursor-pointer' : 'border-gray-300',
          isDragging ? 'ring-2 ring-gray-500 ring-offset-1' : '',
        ].join(' ')}
      >
        <div className="flex flex-col items-center gap-2 text-center">
          <div className="text-sm text-gray-700">{placeholder}</div>
          <div className="text-xs text-gray-500">
            허용: {acceptExt.join(', ')} · 최대 {maxMB}MB
          </div>
        </div>
      </div>

      {/* 실제 파일 입력: 시각적으로 숨김 */}
      <input
        ref={inputRef}
        type="file"
        accept={[...acceptExt, ...acceptMime].join(',')}
        className="hidden"
        multiple={multiple}
        onChange={onInputChange}
      />
    </div>
  )
}