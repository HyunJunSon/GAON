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
  const memberCount = data?.members?.length ?? 0;

  const onSubmit = async (form: AddFamilyInput) => {
    clearError();
    try {
      const res = await addMutation.mutateAsync({ email: form.email });
      if (res) {
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
    <main className="mx-auto w-full max-w-5xl space-y-8 px-4 pb-16 pt-8 md:space-y-10 md:px-0">
      {/* 헤더 섹션 */}
      <header className="rounded-3xl border border-orange-200 bg-gradient-to-br from-orange-50 via-white to-red-100 p-8 shadow-inner">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-500 to-red-500 text-white shadow-lg">
                <svg className="h-7 w-7" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.8}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide text-orange-600">Settings</p>
                <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">가족 구성원 관리</h1>
              </div>
            </div>
            <p className="text-base leading-relaxed text-gray-600 md:text-lg">
              가족 구성원을 초대하고 내 정보를 한눈에 확인하세요.
            </p>
          </div>
          <div className="rounded-2xl border border-white/80 bg-white/70 px-6 py-5 shadow-lg backdrop-blur">
            <p className="text-sm font-medium text-gray-500">현재 가족 구성원</p>
            <div className="mt-3 text-4xl font-bold text-gray-900">{memberCount}</div>
            <p className="text-sm text-gray-500">등록 완료</p>
          </div>
        </div>
      </header>

      <div className="space-y-8">
        {/* 내 정보 섹션 */}
        <section className="rounded-2xl border border-orange-100 bg-white p-8 shadow-lg">
          <div className="mb-6 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-orange-500/20 to-red-500/20 text-orange-600">
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">내 정보</h2>
              <p className="text-sm text-gray-500">연습과 분석 기록에 연결된 계정입니다.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-orange-100 bg-gradient-to-br from-orange-50/60 to-orange-50/30 p-6 transition-all hover:shadow-md">
              <p className="text-sm font-medium text-orange-700 mb-2">이름</p>
              <p className="text-2xl font-semibold text-gray-900">{me?.name ?? '-'}</p>
            </div>
            <div className="rounded-xl border border-orange-100 bg-gradient-to-br from-orange-50/60 to-orange-50/30 p-6 transition-all hover:shadow-md">
              <p className="text-sm font-medium text-orange-700 mb-2">이메일</p>
              <p className="text-2xl font-semibold text-gray-900 break-all">{me?.email ?? '-'}</p>
            </div>
          </div>
        </section>

        {/* 가족 구성원 목록 섹션 */}
        <section className="rounded-2xl border border-orange-100 bg-white p-8 shadow-lg">
          <div className="mb-6 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-orange-500/20 to-red-500/20 text-orange-600">
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">가족 구성원</h2>
              <p className="text-sm text-gray-500">멤버별 권한과 연결 정보를 확인하세요.</p>
            </div>
          </div>

          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="mx-auto mb-3 h-10 w-10 animate-spin rounded-full border-4 border-orange-200 border-t-orange-500" />
                <p className="text-sm text-gray-600">가족 구성원을 불러오는 중...</p>
              </div>
            </div>
          )}

          {isError && (
            <div className="rounded-xl border border-red-200 bg-red-50/80 p-4 text-sm text-red-600">
              <div className="flex items-center gap-2">
                <svg className="h-4 w-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{(error as Error)?.message ?? '가족 구성원을 불러오지 못했어요.'}</span>
              </div>
            </div>
          )}

          {!!data?.members?.length && (
            <div className="space-y-3">
              {data.members.map(m => (
                <div 
                  key={m.id} 
                  className="flex items-center justify-between rounded-xl border border-gray-100 bg-gradient-to-r from-white to-orange-50/40 p-4 shadow-sm transition-all hover:shadow-md hover:border-orange-200"
                >
                  <div className="flex min-w-0 flex-1 items-center gap-4">
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-orange-100 to-red-100 text-orange-600">
                      <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-base font-semibold text-gray-900">{m.name ?? '이름 미입력'}</p>
                      <p className="truncate text-sm text-gray-500">{m.email}</p>
                    </div>
                  </div>
                  <button
                    type="button"
                    disabled={removeMutation.isPending}
                    onClick={() => onRemove(m.id, m.name)}
                    className="ml-4 shrink-0 rounded-xl border border-red-200 bg-red-50 px-4 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-60"
                    aria-label={`${m.name ?? '구성원'} 삭제`}
                  >
                    삭제
                  </button>
                </div>
              ))}
            </div>
          )}

          {!isLoading && !data?.members?.length && !isError && (
            <div className="rounded-xl border border-dashed border-gray-200 bg-gray-50/50 p-12 text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gray-100 text-gray-400">
                <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                </svg>
              </div>
              <p className="text-gray-600">등록된 가족 구성원이 없습니다. 아래에서 초대해보세요.</p>
            </div>
          )}
        </section>

        {/* 가족 구성원 추가 섹션 */}
        <section className="rounded-2xl border border-orange-100 bg-white p-8 shadow-lg">
          <div className="mb-6 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-green-100 to-emerald-100 text-green-700">
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
              </svg>
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">가족 구성원 추가</h2>
              <p className="text-sm text-gray-500">이메일을 입력하면 초대 메일이 발송됩니다.</p>
            </div>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div>
              <label htmlFor="email" className="mb-2 block text-sm font-semibold text-gray-700">
                이메일 주소
              </label>
              <input
                id="email"
                type="email"
                className="w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-900 placeholder:text-gray-400 transition-all focus:border-orange-500 focus:outline-none focus:ring-2 focus:ring-orange-500/20 disabled:bg-gray-50 disabled:text-gray-500"
                placeholder="family@example.com"
                {...register('email')}
                aria-invalid={errors.email ? 'true' : 'false'}
                aria-describedby={errors.email ? 'email-error' : undefined}
              />
              {errors.email && (
                <p id="email-error" className="mt-2 flex items-center gap-1.5 text-sm text-red-600">
                  <svg className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>{errors.email.message}</span>
                </p>
              )}
            </div>

            {serverError && (
              <div className="rounded-xl border border-red-200 bg-red-50/80 p-4">
                <ErrorAlert message={serverError} />
              </div>
            )}

            <button
              type="submit"
              disabled={isSubmitting || addMutation.isPending}
              className="w-full rounded-xl bg-gradient-to-r from-orange-500 to-red-500 px-6 py-3 text-base font-semibold text-white shadow-lg transition-all hover:from-orange-600 hover:to-red-600 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-50"
            >
              {addMutation.isPending ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>추가 중...</span>
                </div>
              ) : (
                '가족 구성원 추가하기'
              )}
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}
