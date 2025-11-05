// 공통 네비게이션에 사용될 링킈 정의
// 라우트 변경시 여기서만 수정하면 됨
import { Home, MessageSquareText, BarChart3, Rocket } from "lucide-react";

export type NavLink = {
  href: string;
  label: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
}

export const NAV_LINKS: NavLink[] = [
  {href: '/', label: '메인', icon: Home},
  {href: '/conversation', label: '대화', icon: MessageSquareText},
  {href: '/analysis', label: '분석', icon: BarChart3},
  {href: '/practice', label: '연습', icon: Rocket},
]

// 인증 페이지(네비 숨김용) 경로
export const AUTH_PAGES = new Set<string>(['/login', '/signup']);