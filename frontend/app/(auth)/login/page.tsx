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
import GaonLogo from '@/components/ui/GaonLogo';

export default function LoginPage() {
  const router = useRouter();
  const { mutate, isPending, isError, error } = useLogin();
  const { serverError, handleError, clearError } = useServerError();
  const { register, handleSubmit, formState: { errors }} = useForm<LoginInput>({
    resolver: zodResolver(LoginSchema),
    mode: 'onChange'
  })
  
  const onSubmit = async (data: LoginInput) => {
    mutate(
      { email: data.email, password: data.password },
      {
        onSuccess: () => {
          clearError();
          router.replace('/');
        },
        onError: handleError,
      },
    )
  }

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
                
                <filter id="glow">
                  <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                  <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                  </feMerge>
                </filter>
              </defs>
              
              <rect width="400" height="400" fill="url(#bgGradient)"/>
              
              <g transform="translate(200, 160)">
                <path d="M 0,25 
                         C -50,0 -75,-5 -75,25
                         C -75,60 -40,90 0,115
                         C 40,90 75,60 75,25
                         C 75,-5 50,0 0,25 Z" 
                      fill="url(#warmGradient)" 
                      opacity="0.3"
                      filter="url(#glow)"/>
                
                <defs>
                  <clipPath id="heartClip">
                    <path d="M 0,25 
                             C -50,0 -75,-5 -75,25
                             C -75,60 -40,90 0,115
                             C 40,90 75,60 75,25
                             C 75,-5 50,0 0,25 Z"/>
                  </clipPath>
                </defs>
                
                <g clipPath="url(#heartClip)">
                  <rect x="-75" y="115" width="150" height="0" fill="url(#warmGradient)" opacity="0.9">
                    <animate attributeName="y" 
                             values="115;-5;115" 
                             dur="4s" 
                             repeatCount="indefinite"/>
                    <animate attributeName="height" 
                             values="0;120;0" 
                             dur="4s" 
                             repeatCount="indefinite"/>
                  </rect>
                </g>
                
                <g transform="translate(0, -10)">
                  <rect x="-3" y="0" width="6" height="60" fill="#FFFFFF" opacity="0.5" rx="3"/>
                  <circle cx="0" cy="65" r="6" fill="#FFFFFF" opacity="0.6"/>
                  <circle cx="0" cy="65" r="4" fill="#FF6B6B" opacity="0.8"/>
                </g>
                
                <circle cx="0" cy="30" r="60" fill="none" stroke="#FFB6B6" strokeWidth="2" opacity="0.3">
                  <animate attributeName="r" values="60;80;60" dur="4s" repeatCount="indefinite"/>
                  <animate attributeName="opacity" values="0.3;0;0.3" dur="4s" repeatCount="indefinite"/>
                </circle>
                <circle cx="0" cy="30" r="60" fill="none" stroke="#FFC8C8" strokeWidth="2" opacity="0.2">
                  <animate attributeName="r" values="60;90;60" dur="4s" begin="1s" repeatCount="indefinite"/>
                  <animate attributeName="opacity" values="0.2;0;0.2" dur="4s" begin="1s" repeatCount="indefinite"/>
                </circle>
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
              
              <text x="200" y="365" 
                    fontFamily="'Noto Sans KR', sans-serif" 
                    fontSize="12" 
                    fontWeight="300" 
                    fill="#999999" 
                    textAnchor="middle"
                    letterSpacing="1">마음의 온도를 측정하여, 온기를 더합니다</text>
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">로그인</h1>
          <p className="text-gray-600">대화에 온도를 더하는 여정을 시작하세요</p>
        </div>

        {/* 로그인 폼 */}
        <div className="bg-white rounded-2xl shadow-lg border border-orange-100 p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div>
              <label htmlFor="email" className="block mb-2 text-sm font-medium text-gray-700">이메일</label>
              <input 
                id="email"
                type="email"
                className='w-full rounded-lg border border-gray-300 px-4 py-3 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-colors'
                placeholder='you@example.com'
                {...register('email')}
              />
              {errors.email && (
                <p className='mt-2 text-sm text-red-600'>{errors.email.message}</p>
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

            <ErrorAlert message={serverError} /> 

            <button 
              type='submit' 
              disabled={isPending} 
              className='w-full rounded-lg bg-gradient-to-r from-orange-500 to-red-500 text-white py-3 font-medium hover:from-orange-600 hover:to-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-md hover:shadow-lg'
            >
              {isPending ? '로그인 중...' : '로그인'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              아직 계정이 없으신가요?{' '}
              <Link href="/signup" className="font-medium text-orange-600 hover:text-orange-700 hover:underline transition-colors">
                회원가입
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
