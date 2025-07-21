'use client';

import React, { useState, useEffect } from 'react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { Bell, Check, CheckCheck, Loader2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { NotificationsService, Notification } from '@/lib/api/notifications';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface NotificationsDropdownProps {
  unreadCount: number;
  onCountChange?: (count: number) => void;
}

export function NotificationsDropdown({ unreadCount, onCountChange }: NotificationsDropdownProps) {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [markingRead, setMarkingRead] = useState<string | null>(null);

  // Load notifications when dropdown opens
  useEffect(() => {
    if (open) {
      loadNotifications();
    }
  }, [open]);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await NotificationsService.getNotifications({ limit: 10 });
      setNotifications(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (notificationId: string) => {
    try {
      setMarkingRead(notificationId);
      await NotificationsService.markNotificationRead(notificationId);

      // Update local state
      setNotifications((prev) =>
        prev.map((n) => (n.id === notificationId ? { ...n, read: true } : n))
      );

      // Update unread count
      if (onCountChange) {
        onCountChange(Math.max(0, unreadCount - 1));
      }
    } catch (err) {
      console.error('Failed to mark notification as read:', err);
    } finally {
      setMarkingRead(null);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      setMarkingRead('all');
      await NotificationsService.markAllNotificationsRead();

      // Update local state
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));

      // Update unread count
      if (onCountChange) {
        onCountChange(0);
      }
    } catch (err) {
      console.error('Failed to mark all as read:', err);
    } finally {
      setMarkingRead(null);
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'task_completed':
        return <CheckCheck className="h-4 w-4 text-green-600" />;
      case 'task_assigned':
        return <Bell className="h-4 w-4 text-blue-600" />;
      case 'comment_added':
      case 'comment_mention':
        return <Bell className="h-4 w-4 text-purple-600" />;
      default:
        return <Bell className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -right-1 -top-1 h-4 w-4 rounded-full bg-destructive text-[10px] font-medium text-destructive-foreground flex items-center justify-center">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <div className="flex items-center justify-between p-3 pb-2">
          <span className="font-semibold">Notifications</span>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-auto p-0 text-xs text-muted-foreground hover:text-foreground"
              onClick={handleMarkAllRead}
              disabled={markingRead === 'all'}
            >
              {markingRead === 'all' ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                'Mark all read'
              )}
            </Button>
          )}
        </div>
        <DropdownMenuSeparator />

        <div className="max-h-[400px] overflow-y-auto">
          {loading ? (
            <div className="p-4 space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="flex items-start space-x-3">
                  <Skeleton className="h-8 w-8 rounded-full" />
                  <div className="flex-1 space-y-1">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-3 w-20" />
                  </div>
                </div>
              ))}
            </div>
          ) : error ? (
            <div className="p-4">
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            </div>
          ) : notifications.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <Bell className="h-8 w-8 mx-auto mb-2 opacity-20" />
              <p className="text-sm">No notifications</p>
            </div>
          ) : (
            <div>
              {notifications.map((notification) => (
                <DropdownMenuItem
                  key={notification.id}
                  className={cn(
                    'flex items-start space-x-3 p-3 cursor-pointer',
                    !notification.read && 'bg-muted/50'
                  )}
                  onClick={() => !notification.read && handleMarkAsRead(notification.id)}
                >
                  <div className="flex-shrink-0 mt-0.5">
                    {getNotificationIcon(notification.type)}
                  </div>
                  <div className="flex-1 space-y-1">
                    <p className="text-sm font-medium leading-none">{notification.title}</p>
                    <p className="text-sm text-muted-foreground">{notification.message}</p>
                    <p className="text-xs text-muted-foreground">
                      {getRelativeTime(notification.created_at)}
                    </p>
                  </div>
                  {!notification.read && markingRead === notification.id && (
                    <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  )}
                  {!notification.read && markingRead !== notification.id && (
                    <Check className="h-4 w-4 text-muted-foreground" />
                  )}
                </DropdownMenuItem>
              ))}
            </div>
          )}
        </div>

        {notifications.length > 0 && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="justify-center text-sm text-muted-foreground">
              View all notifications
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
