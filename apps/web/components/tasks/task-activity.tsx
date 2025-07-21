'use client';

import { useQuery } from '@tanstack/react-query';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Clock,
  Edit3,
  MessageSquare,
  Paperclip,
  UserPlus,
  Calendar,
  Flag,
  CheckCircle2,
  Circle,
  XCircle,
  Share2,
  Trash2,
  Timer,
  GitBranch,
  Target,
  Plus,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import { cn } from '@/lib/utils';
import { Task } from '@/lib/api/tasks';
import { ActivityService, Activity, ActivityType } from '@/services/activity-service';

interface TaskActivityProps {
  taskId: string;
  task: Task;
}

const ActivitySkeleton = () => (
  <div className="flex gap-3 animate-pulse">
    <div className="relative">
      <Skeleton className="h-8 w-8 rounded-full" />
    </div>
    <div className="flex-1 space-y-2">
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-3 w-1/2" />
    </div>
  </div>
);

export function TaskActivity({ taskId, task }: TaskActivityProps) {
  const {
    data: activitiesResponse,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['task-activities', taskId],
    queryFn: () => ActivityService.getTaskActivities(taskId, { limit: 50 }),
    retry: 2,
    staleTime: 30 * 1000, // Consider data fresh for 30 seconds
  });

  const activities = activitiesResponse?.activities || [];

  const getActivityIcon = (type: keyof ActivityType) => {
    switch (type) {
      case 'CREATED':
        return <Plus className="h-4 w-4" />;
      case 'STATUS_CHANGED':
        return <CheckCircle2 className="h-4 w-4" />;
      case 'PRIORITY_CHANGED':
        return <Flag className="h-4 w-4" />;
      case 'ASSIGNED':
      case 'UNASSIGNED':
        return <UserPlus className="h-4 w-4" />;
      case 'DUE_DATE_CHANGED':
      case 'START_DATE_CHANGED':
        return <Calendar className="h-4 w-4" />;
      case 'TITLE_CHANGED':
      case 'DESCRIPTION_CHANGED':
        return <Edit3 className="h-4 w-4" />;
      case 'COMMENT_ADDED':
      case 'COMMENT_EDITED':
      case 'COMMENT_DELETED':
        return <MessageSquare className="h-4 w-4" />;
      case 'ATTACHMENT_ADDED':
      case 'ATTACHMENT_DELETED':
        return <Paperclip className="h-4 w-4" />;
      case 'TIME_LOGGED':
        return <Timer className="h-4 w-4" />;
      case 'DEPENDENCY_ADDED':
      case 'DEPENDENCY_REMOVED':
        return <GitBranch className="h-4 w-4" />;
      case 'SUBTASK_ADDED':
      case 'SUBTASK_REMOVED':
        return <Target className="h-4 w-4" />;
      case 'SHARED':
      case 'UNSHARED':
        return <Share2 className="h-4 w-4" />;
      case 'COMPLETED':
        return <CheckCircle2 className="h-4 w-4" />;
      case 'REOPENED':
        return <Circle className="h-4 w-4" />;
      case 'DELETED':
        return <Trash2 className="h-4 w-4" />;
      default:
        return <Edit3 className="h-4 w-4" />;
    }
  };

  const getActivityColor = (type: keyof ActivityType) => {
    switch (type) {
      case 'CREATED':
        return 'text-green-600 border-green-600';
      case 'STATUS_CHANGED':
      case 'COMPLETED':
        return 'text-blue-600 border-blue-600';
      case 'PRIORITY_CHANGED':
        return 'text-orange-600 border-orange-600';
      case 'ASSIGNED':
      case 'UNASSIGNED':
        return 'text-purple-600 border-purple-600';
      case 'DUE_DATE_CHANGED':
      case 'START_DATE_CHANGED':
        return 'text-yellow-600 border-yellow-600';
      case 'TIME_LOGGED':
        return 'text-indigo-600 border-indigo-600';
      case 'COMMENT_ADDED':
        return 'text-cyan-600 border-cyan-600';
      case 'ATTACHMENT_ADDED':
        return 'text-emerald-600 border-emerald-600';
      case 'SHARED':
        return 'text-pink-600 border-pink-600';
      case 'DELETED':
        return 'text-red-600 border-red-600';
      case 'REOPENED':
        return 'text-gray-600 border-gray-600';
      default:
        return 'text-gray-600 border-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'done':
        return <CheckCircle2 className="h-3 w-3 text-green-600" />;
      case 'in_progress':
        return <Clock className="h-3 w-3 text-blue-600" />;
      case 'cancelled':
        return <XCircle className="h-3 w-3 text-gray-400" />;
      default:
        return <Circle className="h-3 w-3 text-gray-400" />;
    }
  };

  const renderActivityDetails = (activity: Activity) => {
    const { activity_type, old_value, new_value, details } = activity;

    switch (activity_type) {
      case 'STATUS_CHANGED':
        if (old_value && new_value) {
          return (
            <div className="mt-1 flex items-center gap-2">
              <div className="flex items-center gap-1">
                {getStatusIcon(old_value)}
                <span className="text-xs text-muted-foreground">{old_value.replace('_', ' ')}</span>
              </div>
              <span className="text-xs text-muted-foreground">→</span>
              <div className="flex items-center gap-1">
                {getStatusIcon(new_value)}
                <span className="text-xs text-muted-foreground">{new_value.replace('_', ' ')}</span>
              </div>
            </div>
          );
        }
        break;

      case 'PRIORITY_CHANGED':
        if (old_value && new_value) {
          return (
            <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
              <Badge variant="outline" className="text-xs">
                {old_value}
              </Badge>
              <span>→</span>
              <Badge variant="outline" className="text-xs">
                {new_value}
              </Badge>
            </div>
          );
        }
        break;

      case 'COMMENT_ADDED':
        if (details?.comment_content) {
          const preview =
            details.comment_content.length > 100
              ? details.comment_content.slice(0, 100) + '...'
              : details.comment_content;
          return (
            <p className="mt-1 text-xs text-muted-foreground line-clamp-2 bg-muted/50 p-2 rounded">
              "{preview}"
            </p>
          );
        }
        break;

      case 'TIME_LOGGED':
        if (details?.description) {
          return <p className="mt-1 text-xs text-muted-foreground">{details.description}</p>;
        }
        break;

      case 'ATTACHMENT_ADDED':
        if (details?.filename) {
          return (
            <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
              <Paperclip className="h-3 w-3" />
              <span>{details.filename}</span>
              {details?.file_size && (
                <span className="text-xs">({(details.file_size / 1024).toFixed(1)} KB)</span>
              )}
            </div>
          );
        }
        break;

      case 'SUBTASK_ADDED':
        if (details?.subtask_title) {
          return (
            <div className="mt-1 text-xs text-muted-foreground">
              <span className="bg-muted/50 px-2 py-1 rounded">{details.subtask_title}</span>
            </div>
          );
        }
        break;

      case 'DUE_DATE_CHANGED':
        if (old_value || new_value) {
          return (
            <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
              {old_value && (
                <>
                  <span>{format(new Date(old_value), 'MMM d, yyyy')}</span>
                  <span>→</span>
                </>
              )}
              {new_value ? (
                <span>{format(new Date(new_value), 'MMM d, yyyy')}</span>
              ) : (
                <span className="italic">removed</span>
              )}
            </div>
          );
        }
        break;
    }

    return null;
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <ActivitySkeleton key={i} />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <AlertCircle className="mx-auto h-8 w-8 text-destructive/50" />
        <p className="mt-2 text-sm text-muted-foreground">Failed to load activity log</p>
        <button onClick={() => refetch()} className="mt-2 text-xs text-primary hover:underline">
          Try again
        </button>
      </div>
    );
  }

  if (activities.length === 0) {
    return (
      <div className="text-center py-8">
        <Clock className="mx-auto h-8 w-8 text-muted-foreground/50" />
        <p className="mt-2 text-sm text-muted-foreground">No activity recorded yet</p>
        <p className="mt-1 text-xs text-muted-foreground">
          Activities will appear here as you make changes to this task
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Activity count */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {activities.length} {activities.length === 1 ? 'activity' : 'activities'}
        </p>
        {activitiesResponse?.has_next && (
          <button
            onClick={() => {
              // TODO: Implement pagination
            }}
            className="text-xs text-primary hover:underline"
          >
            Load more
          </button>
        )}
      </div>

      {/* Activities list */}
      {activities.map((activity, index) => (
        <div key={activity.id} className="flex gap-3">
          {/* Timeline line */}
          <div className="relative">
            <div
              className={cn(
                'flex h-8 w-8 items-center justify-center rounded-full border-2 bg-background',
                getActivityColor(activity.activity_type)
              )}
            >
              {getActivityIcon(activity.activity_type)}
            </div>
            {index < activities.length - 1 && (
              <div className="absolute left-1/2 top-8 h-full w-px -translate-x-1/2 bg-border" />
            )}
          </div>

          {/* Activity content */}
          <div className="flex-1 pb-8">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  {activity.user && (
                    <Avatar className="h-5 w-5">
                      <AvatarFallback className="text-xs">
                        {activity.user.username.slice(0, 2).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                  )}
                  <p className="text-sm">
                    <span className="font-medium">{activity.user?.username || 'System'}</span>{' '}
                    <span className="text-muted-foreground">
                      {ActivityService.formatActivityDescription(activity)}
                    </span>
                  </p>
                </div>

                {/* Additional details */}
                {renderActivityDetails(activity)}
              </div>

              <div className="flex flex-col items-end gap-1">
                <span className="text-xs text-muted-foreground">
                  {ActivityService.getRelativeTime(activity.created_at)}
                </span>
                <span className="text-xs text-muted-foreground/75">
                  {format(new Date(activity.created_at), 'h:mm a')}
                </span>
              </div>
            </div>
          </div>
        </div>
      ))}

      {/* Success note */}
      <div className="rounded-lg border bg-green-50/50 border-green-200 p-4">
        <p className="text-xs text-green-700">
          <strong>✅ Activity tracking is now live!</strong> All task modifications, comments, and
          interactions are being tracked in real-time.
        </p>
      </div>
    </div>
  );
}
