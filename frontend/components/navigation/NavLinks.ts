// 공통 네비게이션에 사용될 링킈 정의
// 라우트 변경시 여기서만 수정하면 됨
import { Home, MessageSquareText, BarChart3, Rocket } from "lucide-react";
import { usePathname } from "next/navigation";



export type NavLink = {
  href: string;
  label: string;
  isActive: boolean;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
}

// isActive 계산이 없는 기본 링크 정의
type NavLinkBase = Omit<NavLink, 'isActive'>;
const NAV_LINKS_BASE: NavLinkBase[] = [
  { href: '/', label: '메인', icon: Home },
  { href: '/conversation', label: '대화', icon: MessageSquareText },
  { href: '/analysis', label: '분석', icon: BarChart3 },
  { href: '/practice', label: '연습', icon: Rocket },
];

// 주어진 pathname으로 isActive를 계산하여 반환 (퓨어 함수)
export function getNavLinks(pathname: string): NavLink[] {
  return NAV_LINKS_BASE.map((l) => {
    const active =
      l.href === '/'
        ? pathname === '/'
        : pathname.startsWith(l.href);
    return { ...l, isActive: active };
  });
}

// 컴포넌트에서 바로 사용할 수 있는 훅
export function useNavLinks(): NavLink[] {
  const pathname = usePathname();
  return getNavLinks(pathname);
}

// 인증 페이지(네비 숨김용) 경로
export const AUTH_PAGES = new Set<string>(['/login', '/signup']);