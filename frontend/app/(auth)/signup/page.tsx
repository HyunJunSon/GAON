'use client';
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { SignupSchema, type SignupInput } from "@/schemas/validators/auth";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSignup } from "@/hooks/useAuth";

export default function SignupPage() {
  const router = useRouter();
  const { mutate, isPending, isError, error } = useSignup();
  const [serverError, setServerError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { register, handleSubmit, formState: { errors }} = useForm<SignupInput>({
    resolver: zodResolver(SignupSchema),
    mode: 'onChange'
  })
  const onSubmit = async (data: SignupInput) => {
    // try {
    //   setSubmitting(true);
    //   await new Promise((r) => setTimeout(r, 800));
    //   alert(`가입 성공 (mock)\n환영합니다, ${data.name}님!`);
    // } catch (e) {
    //   alert('가입 실패 (mock)');
    // } finally {
    //   setSubmitting(false);
    // }
    mutate(
      { name: data.name, email: data.email, password: data.password, confirmPassword: data.confirmPassword },
      {
        onSuccess: () => {
          // 가입 성공 후: 홈으로 이동하거나 /login 으로 유도
          router.replace('/login');
        },
        onError: (e: unknown) => {
          // ✅ 서버에서 내려준 { message } 우선 사용, 없으면 기본 문구
          let message = '회원가입에 실패했습니다. \n이메일/비밀번호를 확인하거나 잠시 후 다시 시도해주세요.';

          if (e instanceof Error) {
            message = e.message;
          } else if (typeof e === 'object' && e && 'message' in e) {
            message = String((e as { message?: string }).message);
          }

          setServerError(message);
        },
      }
    );
  };

  return (
    <main className="mx-auto max-w-md p-6">
      <h1 className="text-2xl font-semibold mb-4">회원가입</h1>
      <form action="" onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label htmlFor="" className="block mb-1 text-sm">성명</label>
          <input 
            className="w-full rounded border px-3 py-2"
            placeholder="이름을 입력하세요."
            {...register('name')}
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
          )}
        </div>
        <div>
          <label className="block mb-1 text-sm">이메일</label>
          <input
            type="email"
            className="w-full rounded border px-3 py-2"
            placeholder="you@example.com"
            {...register('email')}
          />
          {errors.email && (
            <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
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
        <div>
          <label className="block mb-1 text-sm">비밀번호 확인</label>
          <input
            type="password"
            className="w-full rounded border px-3 py-2"
            placeholder="다시 한 번 비밀번호를 입력하세요."
            {...register('confirmPassword')}
          />
          {errors.confirmPassword && (
            <p className="mt-1 text-sm text-red-600">
              {errors.confirmPassword.message}
            </p>
          )}
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" {...register('termsAgreed')} />
          이용약관에 동의합니다.
        </label>
        {errors.termsAgreed && (
          <p className="mt-1 text-sm text-red-600">
            {errors.termsAgreed.message as string}
          </p>
        )}
        {serverError && (
          <div
            role="alert"
            aria-live="polite"
            className="mb-3 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
          >
            {serverError}
          </div>
        )}   
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded bg-black text-white py-2 disabled:opacity-50"
        >
          {submitting ? '가입 중…' : '가입하기'}
        </button>
      </form>
      <div className="mt-4 text-center">
        <p className="text-sm text-gray-600">
          이미 계정이 없으신가요?{' '}
          <Link href="/login" className="font-medium text-blue-600 hover:underline">
            로그인
          </Link>
        </p>
      </div>
    </main>
  );
}