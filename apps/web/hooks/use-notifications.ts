'use client';

import { useState, useEffect } from 'react';
import { NotificationsService, ActivityItem } from '@/lib/api/notifications';

export function useRecentActivity(limit: number = 5) {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadActivities();
  }, [limit]);

  const loadActivities = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get recent notifications
      const notifications = await NotificationsService.getNotifications({
        limit,
        skip: 0,
      });

      // Transform notifications to activity items
      const activityItems = NotificationsService.notificationsToActivityItems(notifications);
      setActivities(activityItems);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load activities');
      setActivities([]);
    } finally {
      setLoading(false);
    }
  };

  return { activities, loading, error, refetch: loadActivities };
}

export function useNotificationStats() {
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      setError(null);

      const stats = await NotificationsService.getNotificationStats();
      setUnreadCount(stats.unread);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load notification stats');
      setUnreadCount(0);
    } finally {
      setLoading(false);
    }
  };

  return { unreadCount, loading, error, refetch: loadStats };
}
