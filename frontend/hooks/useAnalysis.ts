'use client';

import { AnalysisRes, fetchAnalysis, getConversationId, startAnalysis, StartAnalysisAny } from "@/apis/analysis";
import { qk } from "@/constants/queryKeys";
import { conversationIdStorage } from "@/utils/conversationIdStorage";
import { useMutation, useQuery, UseQueryResult } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { startTransition } from "react";

/**
 * 업로드 → 분석 시작
 * FormData 전송은 내부에서 구성(file, lang 등)
 * 성공 시 /analysis/[conversationId]로 이동
 */
export function useStartAnalysis() {
  const router = useRouter();
  return useMutation({
    mutationFn: async (payload: { file: File; lang?: string }) => {
      const fd = new FormData();
      fd.append('file', payload.file);
      if (payload.lang) fd.append('lang', payload.lang);
      return startAnalysis(fd);
    },
    onSuccess: (res: StartAnalysisAny) => {
      // 백엔드 snake_case 대비 방어
      const id = getConversationId(res);
      conversationIdStorage.set(id);

      // 전환 부드럽게
      router.prefetch(`/analysis`);
      startTransition(() => {
        router.replace(`/analysis`);
      });
    }
  })
}

/** 분석 상세 조회 + 폴링 */
export function useAnalysis(conversationId: string): UseQueryResult<AnalysisRes, Error> {
  return useQuery<AnalysisRes>({
    queryKey: qk.analysis.byId(conversationId),
    queryFn: () => fetchAnalysis(conversationId),
    enabled: !!conversationId,
    retry: false,
    refetchInterval: (query) => {
      if (!query) return 2000;
      const status = query.state.data?.status;
      return status === 'ready' || status === 'completed' || status === 'failed' ? false : 2000;
    },
    staleTime: 0,
  })
}