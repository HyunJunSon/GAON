'use client';

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useNavLinks, AUTH_PAGES, type NavLink } from "./NavLinks";

/**
 * 공통 네비게이션
 * - 모바일: 하단 탭바 (md:hidden)
 * - 태블릿/데스크탑: 좌측 사이드바 (hidden md:flex)
 * - 비로그인/인증 페이지(/login,/signup)에서는 렌더링하지 않음
 * - 현재 경로와 동일한 링크는 비활성화(클릭 무시)
 */
export default function AppNavigation() {
  const pathname = usePathname();
  // 서버에서 받은 초기값으로 state 초기화 → SSR/CSR 일치
  const [authed, setAuthed] = useState<boolean>(false);
  const NAV_LINKS = useNavLinks();
  
  // 토큰 존재 여부로 로그인 상태 추정
  // 외부 변화 구독만 실행
  useEffect(() => {
    if (AUTH_PAGES.has(pathname)) return;

    const id = setTimeout(() => {
      try {
        const s = !!localStorage.getItem('ga_access_token');
        const c = document.cookie.includes('ga_auth=1');
        setAuthed(s || c);
      } catch {
        setAuthed(false);
      }
    }, 0); // ← 이펙트 본문에서 바로 setState 하지 않고, 콜백으로 지연

    return () => clearTimeout(id);
  }, [pathname]);

  // 인증 페이지에서는 네비게이션 숨김
  if (AUTH_PAGES.has(pathname)) return null;
  // 비로그인 상태에서는 네비게이션 숨김
  if (!authed) return null;

  return (
    <>
      {/* 데스크탑/태블릿: 좌측 사이드바 */}
      <aside className="hidden md:flex md:flex-col md:w-56 md:shrink-0 md:border-r md:border-gray-200 md:bg-white">
        <div className="sticky top-0 h-screen p-4">
          <h2 className="mb-4 text-lg font-semibold">GAON</h2>
          <SideNav links={NAV_LINKS} currentPath={pathname} />
        </div>
      </aside>

      {/* 모바일: 하단 탭바 */}
      <BottomTabNav links={NAV_LINKS} currentPath={pathname} />
    
    </>
  )
}

function SideNav ({ links, currentPath }: {links: NavLink[], currentPath: string}) {
  return (
    <nav className="flex flex-col gap-1">
      {links.map(({ href, label, icon: Icon, isActive }) => {
        return (
          <Link
            key={href}
            href={href}
            aria-disabled={isActive}
            onClick={(e) => {
              if (isActive) e.preventDefault(); // 동일 페이지 이동 방지
            }}
            className={[
              'flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition',
              isActive
                ? 'bg-gray-900 text-white cursor-default'
                : 'text-gray-700 hover:bg-gray-100',
            ].join(' ')}
          >
            <Icon className="h-4 w-4" />
            <span>{label}</span>
          </Link>
        );
      })}
    </nav>
  )
}

function BottomTabNav({ links, currentPath }: {links: NavLink[], currentPath: string}) {
  // iOS 안전 영역 대응: safe-area-inset-bottom
  const style = useMemo(
    () => ({ paddingBottom: 'env(safe-area-inset-bottom)' }),
    []
  );
  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-50 border-t border-gray-200 bg-white md:hidden"
      style={style}
    >
      <ul className="mx-auto grid max-w-xl grid-cols-4">
        {links.map(({ href, label, icon: Icon, isActive }) => {
          return (
            <li key={href}>
              <Link
                href={href}
                aria-label={label}
                aria-disabled={isActive}
                onClick={(e) => {
                  if (isActive) e.preventDefault(); // 동일 페이지 이동 방지
                }}
                className={[
                  'flex flex-col items-center justify-center gap-1 py-2 text-xs',
                  isActive ? 'text-gray-900' : 'text-gray-500',
                ].join(' ')}
              >
                <Icon className="h-5 w-5" />
                <span>{label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  )
}