'use client';

import { addFamily, AddFamilyReq, getFamily, GetFamilyRes, removeFamily } from "@/apis/family";
import { qk } from "@/constants/queryKeys";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export function useFamilyList() {
  return useQuery<GetFamilyRes, Error>({
    queryKey: qk.family.list,
    queryFn: getFamily,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });
}

export function useAddFamily() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: AddFamilyReq) => addFamily(body),
    onSuccess: () => {
      // 성공 시 목록 갱신
      qc.invalidateQueries({ queryKey: qk.family.list})
    }
  })
}

export function useRemoveFamily() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (memberId: string) => removeFamily(memberId),
    // ✅ 낙관적 업데이트
    onMutate: async (memberId) => {
      await qc.cancelQueries({ queryKey: qk.family.list });

      const prev = qc.getQueryData<GetFamilyRes>(qk.family.list);
      if (prev) {
        qc.setQueryData<GetFamilyRes>(qk.family.list, {
          members: prev.members.filter(m => String(m.id) !== String(memberId)),
        });
      }
      return { prev };
    },

    onError: (_err, _vars, ctx) => {
      // 롤백
      if (ctx?.prev) qc.setQueryData(qk.family.list, ctx.prev);
    },

    onSuccess: () => {
      // 성공 시 즉시 갱신
      qc.invalidateQueries({ queryKey: qk.family.list });
    },

    onSettled: () => {
      // 서버 정합성 재검증
      qc.invalidateQueries({ queryKey: qk.family.list });
    },
  })
}