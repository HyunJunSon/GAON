// hooks/practice/usePractice.ts
'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { qk } from '@/constants/queryKeys';
import {
  fetchParticipants, startPractice, finishPractice, fetchPracticeResult
} from '@/apis/practice';
import type {
  StartPracticeReq, StartPracticeRes,
  FinishPracticeReq, FinishPracticeRes,
  PracticeResult
} from '@/schemas/practice';

export function useParticipants() {
  return useQuery({
    queryKey: qk.practice.participants,
    queryFn: fetchParticipants,
    staleTime: 5 * 60 * 1000,
  });
}

export function useStartPractice() {
  return useMutation<StartPracticeRes, Error, StartPracticeReq>({
    mutationFn: startPractice,
  });
}

export function useFinishPractice(sessionId: string) {
  const qc = useQueryClient();
  return useMutation<FinishPracticeRes, Error, FinishPracticeReq>({
    mutationFn: (body) => finishPractice(sessionId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: qk.practice.result(sessionId) });
    },
  });
}

export function usePracticeResult(sessionId: string) {
  return useQuery<PracticeResult>({
    queryKey: qk.practice.result(sessionId),
    queryFn: () => fetchPracticeResult(sessionId),
    enabled: !!sessionId,
  });
}