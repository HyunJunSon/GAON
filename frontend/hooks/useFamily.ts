'use client';

import { addFamily, AddFamilyReq, getFamily, GetFamilyRes } from "@/apis/family";
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