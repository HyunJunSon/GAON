'use client';

import ErrorAlert from "@/components/ui/ErrorAlert";
import { useMe } from "@/hooks/useAuth";
import { useAddFamily, useFamilyList, useRemoveFamily } from "@/hooks/useFamily";
import { useServerError } from "@/hooks/useServerError";
import { AddFamilyInput, addFamilySchema } from "@/schemas/validators/family";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

export default function SettingPage() {
  // 1. 가족 구성원 조회
  const { data, isLoading, isError, error } = useFamilyList();
  // 2. 이메일 추가
  const addMutation = useAddFamily();
  // 3. 사용자 정보
  const { data: me } = useMe();
  const removeMutation = useRemoveFamily();

  const { register, handleSubmit, reset, formState: { errors, isSubmitting }} = useForm<AddFamilyInput>({
    resolver: zodResolver(addFamilySchema),
    defaultValues: { email: ''}
  });
  const { serverError, handleError, clearError, setServerError } = useServerError();

  const onSubmit = async (form: AddFamilyInput) => {
    clearError();
    try {
      const res = await addMutation.mutateAsync({ email: form.email });
      if (res.ok) {
        reset({ email: '' });
      } else {
        setServerError('가족 구성원 추가에 실패했습니다.');
      }
    } catch (e) {
      handleError(e);
    }
  };
  
  const onRemove = async (memberId: string, name?: string) => {
    clearError();
    const ok = window.confirm(`${name ?? '구성원'}을(를) 삭제하시겠어요?`);
    if (!ok) return;

    try {
      await removeMutation.mutateAsync(memberId);
      // 낙관적 업데이트 + invalidate 처리로 리스트 갱신됨
    } catch (e) {
      handleError(e);
    }
  };


  return (
    <main className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">설정</h1>
        <p className="text-sm text-gray-600">가족 구성원 관리 및 내 정보 확인</p>
      </header>

      {/* 3) 내 정보 */}
      <section className="rounded border bg-white p-4">
        <h2 className="text-base font-semibold mb-2">내 정보</h2>
        <div className="text-sm text-gray-800">
          <div>이름: <strong>{me?.name ?? '-'}</strong></div>
          <div>이메일: <strong>{me?.email ?? '-'}</strong></div>
        </div>
      </section>

      {/* 1) 가족 구성원 목록 */}
      <section className="rounded border bg-white p-4">
        <h2 className="text-base font-semibold mb-3">가족 구성원</h2>
        {isLoading && <div className="text-sm text-gray-600">가져오는 중…</div>}
        {isError && <div className="text-sm text-red-600">{(error as Error)?.message ?? '조회 실패'}</div>}
        {!!data?.members?.length ? (
          <ul className="divide-y">
            {data.members.map(m => (
              <li key={m.id} className="py-2 flex items-center justify-between">
                <div className="text-sm">
                  <div className="font-medium">{m.name}</div>
                  <div className="text-gray-600">{m.email}</div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    disabled={removeMutation.isPending}
                    onClick={() => onRemove(m.id, m.name)}
                    className="rounded border border-red-300 px-3 py-1 text-xs text-red-600 hover:bg-red-50 disabled:opacity-50"
                    aria-label={`${m.name} 삭제`}
                  >
                    삭제
                  </button>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          !isLoading && <div className="text-sm text-gray-600">구성원이 없습니다.</div>
        )}
      </section>

      {/* 2) 이메일로 가족 계정 추가 */}
      <section className="rounded border bg-white p-4">
        <h2 className="text-base font-semibold mb-3">가족 구성원 추가</h2>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">이메일</label>
            <input
              type="email"
              className="w-full rounded border px-3 py-2 text-sm outline-none focus:ring-2"
              placeholder="family@example.com"
              {...register('email')}
            />
            {errors.email && (
              <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>
            )}
          </div>

          {serverError && <ErrorAlert message={serverError} />}

          <div className="flex items-center gap-2">
            <button
              type="submit"
              disabled={isSubmitting || addMutation.isPending}
              className="rounded bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              {addMutation.isPending ? '추가 중…' : '추가하기'}
            </button>
          </div>
        </form>
      </section>
    </main>
  )
}