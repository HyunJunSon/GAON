// components/navigation/GlobalHeader.tsx
'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useMounted } from '@/hooks/useMounted';
import { authStorage } from '@/utils/authStorage';
import { useLogout, useMe } from '@/hooks/useAuth';
import GaonLogo from '@/components/ui/GaonLogo';

const AUTH_PAGES = new Set(['/login', '/signup']);

export default function GlobalHeader() {
  const pathname = usePathname();
  const mounted = useMounted();
  const router = useRouter();
  const { mutate: logout, isPending } = useLogout();
  const { data: me } = useMe();

  // 인증 페이지에서는 헤더 숨김
  if (AUTH_PAGES.has(pathname)) return null;

  // 마운트 전에는 토큰 판별하지 않아 mismatch 회피
  const authed = mounted
    ? !!authStorage.get() || document.cookie.includes('ga_auth=1')
    : false;

  const onLogout = () => {
    // useLogout 훅: 성공 시 authStorage.clear() + me 캐시 제거 이미 구현됨
    logout(undefined, {
      onSuccess: () => {
        // 필요 시 쿠키도 함께 소거(목업 단계면 생략 가능)
        // document.cookie = 'ga_auth=; Max-Age=0; path=/';
        router.replace('/login');
      },
    });
  };

  return (
    <header className="sticky top-0 z-30 shrink-0 border-b border-orange-100 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/80 shadow-sm">
      <div className="mx-4 flex h-14 items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl font-bold bg-gradient-to-r from-orange-500 to-red-500 bg-clip-text text-transparent">GAON</span>
        </div>

        {/* 우측 액션: 로그인 상태에서만 노출 */}
        {authed && (
          <div className="flex items-center gap-3">
            {me && (
              <div className="text-right text-xs text-gray-600 mr-1">
                <div className="font-medium">{me.name}</div>
                <div className="text-[10px] text-gray-500">{me.email}</div>
              </div>
            )}
            <button
              type="button"
              onClick={onLogout}
              disabled={isPending}
              className="px-3 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-orange-50 rounded-lg transition-all duration-200 disabled:opacity-50 flex items-center gap-1"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              {isPending ? '로그아웃 중…' : '로그아웃'}
            </button>
          </div>
        )}
      </div>
    </header>
  );
}