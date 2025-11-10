'use client';

import { useState, useEffect, useCallback } from 'react';
import { usePathname } from 'next/navigation';
import { apiFetch } from '@/apis/client';

interface User {
  id: number;
  email: string;
  name: string;
}

export function UserInfo() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const pathname = usePathname();

  const fetchUserInfo = useCallback(async () => {
    try {
      const userData = await apiFetch<User>('/api/auth/me');
      setUser(userData);
    } catch (error) {
      console.error('사용자 정보 조회 실패:', error);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // 로그인/회원가입 페이지에서는 API 호출하지 않음
    const hideOnPages = ['/login', '/signup'];
    if (!hideOnPages.includes(pathname)) {
      fetchUserInfo();
    } else {
      setLoading(false);
    }
  }, [pathname, fetchUserInfo]);

  // 로그인/회원가입 페이지에서는 숨기기
  const hideOnPages = ['/login', '/signup'];
  if (hideOnPages.includes(pathname)) {
    return null;
  }

  const handleLogout = async () => {
    try {
      await apiFetch('/api/auth/logout', { method: 'POST' });
      localStorage.removeItem('token');
      window.location.href = '/login';
    } catch (error) {
      console.error('로그아웃 실패:', error);
      // 토큰만 제거하고 로그인 페이지로 이동
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center space-x-2">
        <div className="w-8 h-8 bg-gray-200 rounded-full animate-pulse"></div>
        <div className="w-20 h-4 bg-gray-200 rounded animate-pulse"></div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="flex items-center space-x-3">
      <div className="flex items-center space-x-2">
        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
          {user.name.charAt(0)}
        </div>
        <span className="text-sm font-medium text-gray-700">{user.name}</span>
      </div>
      <button
        onClick={handleLogout}
        className="text-xs text-gray-500 hover:text-gray-700 px-2 py-1 rounded hover:bg-gray-100"
      >
        로그아웃
      </button>
    </div>
  );
}
