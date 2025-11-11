// components/navigation/GlobalHeader.tsx
'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useMounted } from '@/hooks/useMounted';
import { authStorage } from '@/utils/authStorage';
import { useLogout, useMe } from '@/hooks/useAuth'; // 이미 있으므로 재사용

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
    <header className="sticky top-0 z-30 border-b bg-white/80 backdrop-blur supports-[backdrop-filter]:bg-white/60">
      <div className="mx-4 flex h-12 items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold">GAON</h2>
        </div>

        {/* 우측 액션: 로그인 상태에서만 노출 */}
        {authed && (
          <div className="flex items-center gap-2">
            {me && (
              <div className="text-right text-xs text-gray-600 mr-2">
                <div>{me.name}</div>
                <div className="text-[10px] text-gray-500">{me.email}</div>
              </div>
            )}
            {/* 추후 프로필/설정 드롭다운으로 확장 가능 */}
            <button
              type="button"
              onClick={onLogout}
              disabled={isPending}
              className="rounded px-3 py-1 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50 text-sm cursor-pointer"
            >
              {isPending ? '로그아웃 중…' : '로그아웃'}
            </button>
          </div>
        )}
      </div>
    </header>
  );
}