'use client';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { LoginSchema, type LoginInput } from '@/schemas/validators/auth';
import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useLogin } from '@/hooks/useAuth';

export default function LoginPage() {
  const router = useRouter();
  const { mutate, isPending, isError, error } = useLogin();
  const [serverError, setServerError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { register, handleSubmit, formState: { errors }} = useForm<LoginInput>({
    resolver: zodResolver(LoginSchema),
    mode: 'onChange'
  })
  // 지금은 목업: 실제 API 연동 전까지 setTimeout으로 성공/실패 UX 확인
  const onSubmit = async (data: LoginInput) => {
    // try {
    //   setSubmitting(true);
    //   await new Promise((r) => setTimeout(r, 800))
    //   alert(`로그인 성공 (mock)\nemail: ${data.email}`)
    // } catch (e) {
    //   alert('로그인 실패 (mock)')
    // } finally {
    //   setSubmitting(false);
    // }
    mutate(
      { email: data.email, password: data.password },
      {
        onSuccess: () => {
          // ✅ 성공 시 서버 에러 초기화
          setServerError(null);
          // 로그인 성공 후 이동(필요에 맞게 경로 조정)
          router.replace('/');
        },
        onError: (e: unknown) => {
          // ✅ 서버에서 내려준 { message } 우선 사용, 없으면 기본 문구
          let message = '로그인에 실패했습니다. \n이메일/비밀번호를 확인하거나 잠시 후 다시 시도해주세요.';

          if (e instanceof Error) {
            message = e.message;
          } else if (typeof e === 'object' && e && 'message' in e) {
            message = String((e as { message?: string }).message);
          }

          setServerError(message);
        },
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
        {serverError && (
          <div
            role="alert"
            aria-live="polite"
            className="mb-3 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
          >
            {serverError}
          </div>
        )}    
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