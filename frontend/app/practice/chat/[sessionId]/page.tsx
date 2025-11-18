// app/practice/chat/[sessionId]/page.tsx
'use client';

import { useState } from 'react';
import { useParams, useSearchParams, useRouter } from 'next/navigation';
import { useSubmitPracticeLogs } from '@/hooks/usePractice';

type PracticeMode = 'chat' | 'voice';

type ChatRole = 'user' | 'assistant';

type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: string;
};

/**
 * /practice/chat/[sessionId]
 * - 쿼리 파라미터 mode에 따라 두 가지 모드로 동작
 *   - mode=chat  → 텍스트 채팅 연습
 *   - mode=voice → 음성 대화 연습(1차 버전: UI만)
 *
 * 이 페이지는 아직 목업 단계로,
 * - LLM/서버 연동 없이 로컬 state로만 메시지를 관리한다.
 * - 나중에 FastAPI WebSocket/HTTP API와 연결할 예정.
 */
export default function PracticeChatPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const sp = useSearchParams();
  const router = useRouter();

  // 쿼리에서 mode 읽기, 기본값은 chat
  const modeParam = sp.get('mode');
  const mode: PracticeMode =
    modeParam === 'voice' ? 'voice' : 'chat'; // 잘못된 값이면 기본값은 chat으로 처리

  return (
    // <main className="mx-auto flex h-[calc(100dvh-56px)] min-h-0 max-w-3xl flex-col p-4 md:p-6">      
    // <main className="flex h-[calc(100dvh-120px)] min-h-5 max-w-3xl flex-col p-4 md:p-6">
    <main className="mx-auto flex max-w-3xl flex-col gap-4 p-4 md:p-6">
    {/* 상단 헤더 영역 */}
      <header className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold">연습 세션</h1>
          <p className="text-xs text-gray-500">
            세션 ID: <span className="font-mono">{sessionId}</span>
          </p>
          <p className="mt-1 text-xs text-gray-600">
            현재 모드:{' '}
            <span className="font-medium">
              {mode === 'chat' ? '실시간 채팅 연습' : '음성 대화 연습'}
            </span>
          </p>
        </div>
      </header>

      {/* 모드에 따라 다른 UI 렌더 */}
      {mode === 'chat' ? (
        <ChatMode />
      ) : (
        <VoiceMode />
      )}
    </main>
  );
}

/**
 * 💬 텍스트 채팅 모드
 * - 로컬 state로 메시지 목록 관리
 * - 목업 assistant 응답
 */
function ChatMode() {
  const router = useRouter();
  const { sessionId } = useParams<{ sessionId: string}>();
  const submitLogs = useSubmitPracticeLogs(sessionId);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'm1',
      role: 'assistant',
      content: '이번 연습에서는 실제 가족에게 말하듯이 이야기해볼게요. 먼저, 어떤 상황을 다시 연습해보고 싶나요?',
      createdAt: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isComposing, setIsComposing] = useState(false);

  // 메시지 전송 핸들러
  function handleSend() {
    const trimmed = input.trim();
    if (!trimmed) return;

    const now = new Date().toISOString();

    const userMsg: ChatMessage = {
      id: `u_${now}`,
      role: 'user',
      content: trimmed,
      createdAt: now,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');

    // 목업 assistant 응답 (나중에 LLM 응답으로 교체 예정)
    setTimeout(() => {
      const assistantMsg: ChatMessage = {
        id: `a_${Date.now()}`,
        role: 'assistant',
        content:
          '그렇게 느낄 수 있어요. 그때 가족에게 어떤 말부터 건네고 싶으세요?',
        createdAt: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    }, 600);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // 한글 IME 조합 중일 때는 Enter를 전송으로 쓰지 않기
    const nativeEvent = e.nativeEvent as KeyboardEvent & { isComposing?: boolean};
    if (nativeEvent.isComposing || isComposing) {
      return;
    }

    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  async function handleFinishClick() {
    if (submitLogs.isPending) return;

    try {
      // 서버에 보낼 형태로 매핑 (id는 필요 없으니 제외)
      const payload = messages.map((m) => ({
        role: m.role,
        content: m.content,
        createdAt: m.createdAt,
      }));

      await submitLogs.mutateAsync(payload);
      router.push(`/practice/result/${sessionId}`);
    } catch (e) {
      // TODO: 공통 에러 핸들링 훅으로 바꿀 수 있음
      console.error('연습 로그 전송 실패:', e);
      alert('연습 결과 분석 요청에 실패했어요. 잠시 후 다시 시도해주세요.');
    }
  }

  return (
    <section className="flex flex-1 min-h-[68vh] max-h-[68vh] flex-col rounded-xl border bg-white p-3 md:p-4">
      {/* 메시지 리스트 */}
      <div className="mb-3 flex-1 min-h-0 space-y-3 overflow-y-auto pr-1">
        {messages.map((m) => (
          <ChatBubble key={m.id} message={m} />
        ))}
      </div>

      {/* 입력창 + 연습 종료 버튼 */}
      <div className="border-t pt-3">
        <label className="mb-1 block text-xs font-medium text-gray-600">
          지금 떠오르는 말, 그대로 적어보세요.
        </label>
        <div className="flex flex-col gap-2 md:flex-row">
          <textarea
            className="min-h-[60px] flex-1 resize-none rounded-lg border border-gray-300 p-2 text-sm outline-none focus:border-black focus:ring-1 focus:ring-black/10"
            placeholder="예: 그때는 내가 너무 몰아붙였던 것 같아…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            onCompositionStart={() => setIsComposing(true)}
            onCompositionEnd={() => setIsComposing(false)}
          />
          <div className="flex shrink-0 gap-2">
            <button
              type="button"
              onClick={handleSend}
              disabled={!input.trim()}
              className="h-[60px] flex-1 rounded-lg bg-black px-3 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-gray-400"
            >
              보내기
            </button>
            <button
              type="button"
              onClick={handleFinishClick}
              disabled={submitLogs.isPending}
              className="h-[60px] flex-1 rounded-lg border border-gray-300 bg-white px-3 text-sm font-medium text-gray-800 hover:border-red-500 hover:text-red-600 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {submitLogs.isPending ? '분석 요청 중…' : '연습 종료하기'}
            </button>
          </div>
        </div>
        <p className="mt-1 text-[11px] text-gray-400">
          Enter: 전송 / Shift + Enter: 줄바꿈
        </p>
      </div>
    </section>
  );
}

/**
 * 채팅 말풍선 UI
 */
function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';

  return (
    <div
      className={`flex ${
        isUser ? 'justify-end' : 'justify-start'
      }`}
    >
      <div
        className={[
          'max-w-[80%] rounded-2xl px-3 py-2 text-sm shadow-sm',
          isUser
            ? 'rounded-br-sm bg-black text-white'
            : 'rounded-bl-sm bg-gray-100 text-gray-900',
        ].join(' ')}
      >
        <p className="whitespace-pre-line">{message.content}</p>
      </div>
    </div>
  );
}

/**
 * 🎙️ 음성 대화 모드 (1차 버전: UI 골격만)
 * - 추후 Web Speech API / 서버 STT 연동을 위한 자리
 */
function VoiceMode() {
  return (
    <section className="flex flex-1 flex-col items-center justify-center rounded-xl border bg-white p-6 text-center">
      <h2 className="text-lg font-semibold">음성 대화 연습</h2>
      <p className="mt-2 text-sm text-gray-600">
        마이크를 통해 실제 대화처럼 말하기 연습을 할 수 있는 모드입니다.
      </p>

      <div className="mt-8 flex flex-col items-center gap-4">
        <div className="flex h-24 w-24 items-center justify-center rounded-full border border-dashed border-gray-400 bg-gray-50">
          <span className="text-xs text-gray-500">마이크 아이콘 자리</span>
        </div>
        <p className="text-xs text-gray-500">
          음성 인식/합성 기능은 추후 단계에서 연결할 예정이에요.
          <br />
          먼저 채팅 모드에서 대화 내용을 다듬어 보는 것부터 시작해 보세요.
        </p>
      </div>
    </section>
  );
}