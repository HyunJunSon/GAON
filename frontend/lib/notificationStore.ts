import { create } from 'zustand';

export type NotificationType = 'success' | 'error' | 'info' | 'warning';

export type Notification = {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  conversationId?: string;
  link?: string;
  isRead: boolean;
  createdAt: Date;
  // 가족 초대 관련 필드
  inviteId?: number;
  inviterName?: string;
  familyName?: string;
  actionType?: 'family_invite';
};

type NotificationStore = {
  notifications: Notification[];
  unreadCount: number;
  
  // Actions
  addNotification: (notification: Omit<Notification, 'id' | 'isRead' | 'createdAt'>) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
};

export const useNotificationStore = create<NotificationStore>((set, get) => ({
  notifications: [],
  unreadCount: 0,

  addNotification: (notification) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString(),
      isRead: false,
      createdAt: new Date(),
    };

    set((state) => {
      const newNotifications = [newNotification, ...state.notifications];
      return {
        notifications: newNotifications,
        unreadCount: newNotifications.filter(n => !n.isRead).length,
      };
    });

    // 브라우저 알림 표시
    if (Notification.permission === 'granted') {
      new Notification(notification.title, {
        body: notification.message,
        icon: '/favicon.ico',
        tag: notification.conversationId || 'gaon-notification',
      });
    }
  },

  markAsRead: (id) => {
    set((state) => {
      const updatedNotifications = state.notifications.map(n =>
        n.id === id ? { ...n, isRead: true } : n
      );
      return {
        notifications: updatedNotifications,
        unreadCount: updatedNotifications.filter(n => !n.isRead).length,
      };
    });
  },

  markAllAsRead: () => {
    set((state) => ({
      notifications: state.notifications.map(n => ({ ...n, isRead: true })),
      unreadCount: 0,
    }));
  },

  removeNotification: (id) => {
    set((state) => {
      const filteredNotifications = state.notifications.filter(n => n.id !== id);
      return {
        notifications: filteredNotifications,
        unreadCount: filteredNotifications.filter(n => !n.isRead).length,
      };
    });
  },

  clearAll: () => {
    set({
      notifications: [],
      unreadCount: 0,
    });
  },
}));
