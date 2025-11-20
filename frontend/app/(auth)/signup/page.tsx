'use client';
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { SignupSchema, type SignupInput } from "@/schemas/validators/auth";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSignup } from "@/hooks/useAuth";
import { useServerError } from "@/hooks/useServerError";
import ErrorAlert from "@/components/ui/ErrorAlert";

export default function SignupPage() {
  const router = useRouter();
  const { mutate, isPending, isError, error } = useSignup();
  const { serverError, handleError, clearError } = useServerError()
  const [submitting, setSubmitting] = useState(false);
  const { register, handleSubmit, formState: { errors }} = useForm<SignupInput>({
    resolver: zodResolver(SignupSchema),
    mode: 'onChange'
  })
  
  const onSubmit = async (data: SignupInput) => {
    mutate(
      { 
        name: data.name, 
        email: data.email, 
        birthdate: data.birthdate,
        gender: data.gender,
        password: data.password, 
        confirmPassword: data.confirmPassword, 
        termsAgreed: data.termsAgreed 
      },
      {
        onSuccess: () => {
          clearError();
          router.replace('/login');
        },
        onError: handleError,
      }
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-red-50 flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        {/* 로고 섹션 */}
        <div className="text-center mb-8">
          <div className="w-72 h-72 mx-auto mb-4">
            <svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
              <defs>
                <linearGradient id="warmGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style={{stopColor:'#FF6B6B', stopOpacity:1}} />
                  <stop offset="50%" style={{stopColor:'#FFA07A', stopOpacity:1}} />
                  <stop offset="100%" style={{stopColor:'#FFD93D', stopOpacity:1}} />
                </linearGradient>
                
                <radialGradient id="bgGradient" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" style={{stopColor:'#FFF5F5', stopOpacity:1}} />
                  <stop offset="100%" style={{stopColor:'#FFFFFF', stopOpacity:1}} />
                </radialGradient>
              </defs>
              
              <rect width="400" height="400" fill="url(#bgGradient)"/>
              
              <g transform="translate(200, 160)">
                <path d="M 0,25 
                         C -50,0 -75,-5 -75,25
                         C -75,60 -40,90 0,115
                         C 40,90 75,60 75,25
                         C 75,-5 50,0 0,25 Z" 
                      fill="url(#warmGradient)" 
                      opacity="0.4"/>
                
                <g transform="translate(0, -10)">
                  <rect x="-3" y="0" width="6" height="60" fill="#FFFFFF" opacity="0.5" rx="3"/>
                  <circle cx="0" cy="65" r="6" fill="#FFFFFF" opacity="0.6"/>
                  <circle cx="0" cy="65" r="4" fill="#FF6B6B" opacity="0.8"/>
                </g>
              </g>
              
              <g opacity="0.4">
                <line x1="120" y1="180" x2="180" y2="180" stroke="#FF8C8C" strokeWidth="1.5"/>
                <line x1="220" y1="180" x2="280" y2="180" stroke="#FF8C8C" strokeWidth="1.5"/>
                <circle cx="120" cy="180" r="3" fill="#FF8C8C"/>
                <circle cx="280" cy="180" r="3" fill="#FF8C8C"/>
              </g>
              
              <defs>
                <linearGradient id="textGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" style={{stopColor:'#FF8C8C', stopOpacity:1}} />
                  <stop offset="50%" style={{stopColor:'#FF6B6B', stopOpacity:1}} />
                  <stop offset="100%" style={{stopColor:'#E85858', stopOpacity:1}} />
                </linearGradient>
              </defs>
              
              <text x="200" y="310" 
                    fontFamily="'Quicksand', 'Fredoka', 'Nunito', sans-serif" 
                    fontSize="48" 
                    fontWeight="700" 
                    fill="url(#textGradient)" 
                    textAnchor="middle"
                    letterSpacing="6">GAON</text>
              
              <text x="200" y="340" 
                    fontFamily="'Noto Serif KR', serif" 
                    fontSize="22" 
                    fontWeight="400" 
                    fill="#FF8C8C" 
                    textAnchor="middle"
                    letterSpacing="2">加溫</text>
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">회원가입</h1>
          <p className="text-gray-600">따뜻한 대화의 시작, 함께해요</p>
        </div>

        {/* 회원가입 폼 */}
        <div className="bg-white rounded-2xl shadow-lg border border-orange-100 p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div>
              <label htmlFor="name" className="block mb-2 text-sm font-medium text-gray-700">성명</label>
              <input 
                id="name"
                className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors"
                placeholder="이름을 입력하세요"
                {...register('name')}
              />
              {errors.name && (
                <p className="mt-2 text-sm text-red-600">{errors.name.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="email" className="block mb-2 text-sm font-medium text-gray-700">이메일</label>
              <input
                id="email"
                type="email"
                className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors"
                placeholder="you@example.com"
                {...register('email')}
              />
              {errors.email && (
                <p className="mt-2 text-sm text-red-600">{errors.email.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="birthdate" className="block mb-2 text-sm font-medium text-gray-700">생년월일</label>
              <input
                id="birthdate"
                type="date"
                className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors"
                {...register('birthdate')}
              />
              {errors.birthdate && (
                <p className="mt-2 text-sm text-red-600">{errors.birthdate.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="gender" className="block mb-2 text-sm font-medium text-gray-700">성별</label>
              <select
                id="gender"
                className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors"
                {...register('gender')}
              >
                <option value="">선택하세요</option>
                <option value="Male">남성</option>
                <option value="Female">여성</option>
                <option value="Other">기타</option>
              </select>
              {errors.gender && (
                <p className="mt-2 text-sm text-red-600">{errors.gender.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="block mb-2 text-sm font-medium text-gray-700">비밀번호</label>
              <input
                id="password"
                type="password"
                className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors"
                placeholder="비밀번호를 입력하세요"
                {...register('password')}
              />
              {errors.password && (
                <p className="mt-2 text-sm text-red-600">
                  {errors.password.message}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block mb-2 text-sm font-medium text-gray-700">비밀번호 확인</label>
              <input
                id="confirmPassword"
                type="password"
                className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors"
                placeholder="다시 한 번 비밀번호를 입력하세요"
                {...register('confirmPassword')}
              />
              {errors.confirmPassword && (
                <p className="mt-2 text-sm text-red-600">
                  {errors.confirmPassword.message}
                </p>
              )}
            </div>

            <div className="flex items-start gap-3">
              <input 
                id="terms"
                type="checkbox" 
                className="mt-1 w-4 h-4 text-orange-600 bg-gray-100 border-gray-300 rounded focus:ring-orange-500 focus:ring-2"
                {...register('termsAgreed')} 
              />
              <label htmlFor="terms" className="text-sm text-gray-700">
                <span className="font-medium">이용약관</span>에 동의합니다.
              </label>
            </div>
            {errors.termsAgreed && (
              <p className="text-sm text-red-600">
                {errors.termsAgreed.message as string}
              </p>
            )}

            <ErrorAlert message={serverError}/>

            <button
              type="submit"
              disabled={isPending}
              className="w-full rounded-lg bg-gradient-to-r from-orange-500 to-red-500 text-white py-3 font-medium hover:from-orange-600 hover:to-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-md hover:shadow-lg"
            >
              {isPending ? '가입 중…' : '가입하기'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              이미 계정이 있으신가요?{' '}
              <Link href="/login" className="font-medium text-orange-600 hover:text-orange-700 hover:underline transition-colors">
                로그인
              </Link>
            </p>
          </div>
        </div>

        {/* 하단 메시지 */}
        <div className="text-center mt-6">
          <p className="text-xs text-gray-500">
            AI 기반 대화 분석으로 인간관계에 따뜻함을 더하는 서비스
          </p>
        </div>
      </div>
    </div>
  );
}
