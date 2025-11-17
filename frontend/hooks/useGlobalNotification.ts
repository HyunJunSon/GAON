import { useEffect } from 'react';

interface NotificationOptions {
  title: string;
  body: string;
  icon?: string;
  onClick?: () => void;
}

export function useGlobalNotification() {
  useEffect(() => {
    // 브라우저 알림 권한 요청
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  const showNotification = ({ title, body, icon, onClick }: NotificationOptions) => {
    // 1. 기존 NotificationCenter에 알림 추가
    try {
      // notificationStore 사용 (이미 있는 시스템)
      const { addNotification } = require('@/lib/notificationStore');
      addNotification({
        id: Date.now().toString(),
        title,
        message: body,
        type: 'success',
        timestamp: new Date(),
        onClick
      });
    } catch (error) {
      console.warn('기존 알림 시스템 사용 실패, fallback 사용');
    }

    // 2. 브라우저 알림 (백그라운드용)
    if ('Notification' in window && Notification.permission === 'granted') {
      const notification = new Notification(title, {
        body,
        icon: icon || '/favicon.ico',
        badge: '/favicon.ico',
        tag: 'gaon-analysis',
      });

      if (onClick) {
        notification.onclick = () => {
          window.focus();
          onClick();
          notification.close();
        };
      }

      setTimeout(() => notification.close(), 5000);
    }
  };

  return { showNotification };
}
