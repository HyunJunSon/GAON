'use client';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { LoginSchema, type LoginInput } from '@/schemas/validators/auth';
import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useLogin } from '@/hooks/useAuth';
import { useServerError } from '@/hooks/useServerError';
import ErrorAlert from '@/components/ui/ErrorAlert';

export default function LoginPage() {
  const router = useRouter();
  const { mutate, isPending, isError, error } = useLogin();
  const { serverError, handleError, clearError } = useServerError();
  const { register, handleSubmit, formState: { errors }} = useForm<LoginInput>({
    resolver: zodResolver(LoginSchema),
    mode: 'onChange'
  })
  // 지금은 목업: 실제 API 연동 전까지 setTimeout으로 성공/실패 UX 확인
  const onSubmit = async (data: LoginInput) => {
    mutate(
      { email: data.email, password: data.password },
      {
        onSuccess: () => {
          // ✅ 성공 시 서버 에러 초기화
          clearError();
          // 로그인 성공 후 이동(필요에 맞게 경로 조정)
          router.replace('/');
        },
        onError: handleError,
      },
    )
  }
  return (
    <main className="mx-auto max-w-md p-6">
      <h1 className="text-2xl font-semibold mb-4">로그인</h1>        
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label htmlFor="" className="block mb-1 text-sm">이메일</label>
          <input 
            type="email"
            className='w-full rounded border px-3 py-2'
            placeholder='you@example.com'
            {...register('email')}
          />
          {errors.email && (
            <p className='mt-1 text-sm text-red-600'>{errors.email.message}</p>
          )}
        </div>
        <div>
          <label className="block mb-1 text-sm">비밀번호</label>
          <input
            type="password"
            className="w-full rounded border px-3 py-2"
            placeholder="비밀번호를 입력하세요."
            {...register('password')}
          />
          {errors.password && (
            <p className="mt-1 text-sm text-red-600">
              {errors.password.message}
            </p>
          )}
        </div>
        <ErrorAlert message={serverError} /> 
        <button type='submit' disabled={isPending} className='w-full rounded bg-black text-white py-2 disabled:opacity-50'>
          {isPending ? '로그인 중...' : '로그인'}
        </button>
      </form>
      <div className="mt-4 text-center">
        <p className="text-sm text-gray-600">
          아직 계정이 없으신가요?{' '}
          <Link href="/signup" className="font-medium text-blue-600 hover:underline">
            회원가입
          </Link>
        </p>
      </div>
    </main>
  );
}