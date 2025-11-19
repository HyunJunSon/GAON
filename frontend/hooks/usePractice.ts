// hooks/practice/usePractice.ts
'use client';

import { useQuery, useMutation, useQueryClient, UseQueryResult } from '@tanstack/react-query';
import { qk } from '@/constants/queryKeys';
import {
  fetchParticipants, startPractice, finishPractice, fetchPracticeResult,
  startPracticeSession, submitPracticeLogs
} from '@/apis/practice';
import type {
  StartPracticeReq, StartPracticeRes,
  FinishPracticeReq, FinishPracticeRes,
  PracticeResult, PracticeChatMessage
} from '@/schemas/practice';

export function useParticipants() {
  return useQuery({
    queryKey: qk.practice.participants,
    queryFn: fetchParticipants,
    staleTime: 5 * 60 * 1000,
  });
}

// export function useStartPractice() {
//   return useMutation<StartPracticeRes, Error, StartPracticeReq>({
//     mutationFn: startPractice,
//   });
// }

export function useFinishPractice(sessionId: string) {
  const qc = useQueryClient();
  return useMutation<FinishPracticeRes, Error, FinishPracticeReq>({
    mutationFn: (body) => finishPractice(sessionId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.practice.result(sessionId) });
    },
  });
}

// export function usePracticeResult(sessionId: string) {
//   return useQuery<PracticeResult>({
//     queryKey: qk.practice.result(sessionId),
//     queryFn: () => fetchPracticeResult(sessionId),
//     enabled: !!sessionId,
//   });
// }

/**
 * 연습 세션 생성 훅
 * - /practice 페이지에서 "실시간 채팅/음성대화로 연습하기" 클릭 시 사용
 */
export function useStartPracticeSession() {
  return useMutation<StartPracticeRes, Error, StartPracticeReq>({
    mutationFn: (payload) => startPracticeSession(payload),
  });
}

/**
 * 연습 결과 조회 훅
 * - /practice/result/[sessionId] 페이지에서 사용
 */
export function usePracticeResult(sessionId: string): UseQueryResult<PracticeResult, Error> {
  return useQuery<PracticeResult, Error>({
    queryKey: ['practice', 'result', sessionId],
    queryFn: () => fetchPracticeResult(sessionId),
    enabled: !!sessionId,
  });
}

/**
 * 연습 세션 로그 제출 훅
 * - /practice/chat/[sessionId]에서 사용
 */
export function useSubmitPracticeLogs(sessionId: string) {
  return useMutation<void, Error, PracticeChatMessage[]>({
    mutationFn: (messages) => submitPracticeLogs(sessionId, messages),
  });
}