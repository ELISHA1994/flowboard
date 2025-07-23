'use client';

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertCircle,
  Calendar,
  Clock,
  Edit,
  Trash2,
  User,
  FolderOpen,
  Tag,
  MoreVertical,
  CheckCircle2,
  Circle,
  Pause,
  X,
  AlertTriangle,
} from 'lucide-react';

import { CalendarEvent, formatEventTime } from '@/lib/calendar/calendar-utils';
import { TaskStatus } from '@/lib/api/tasks';
import { useCalendarOperations } from '@/hooks/use-calendar-tasks';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';

interface TaskDetailModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  event: CalendarEvent | null;
  onSuccess?: () => void;
  onEdit?: (event: CalendarEvent) => void;
}

// Status change options
const statusChangeOptions = [
  {
    value: 'todo' as TaskStatus,
    label: 'Mark as To Do',
    icon: Circle,
    color: 'text-gray-500',
  },
  {
    value: 'in_progress' as TaskStatus,
    label: 'Mark as In Progress',
    icon: Clock,
    color: 'text-amber-500',
  },
  {
    value: 'done' as TaskStatus,
    label: 'Mark as Done',
    icon: CheckCircle2,
    color: 'text-green-500',
  },
  {
    value: 'cancelled' as TaskStatus,
    label: 'Mark as Cancelled',
    icon: X,
    color: 'text-violet-500',
  },
];

const priorityColors = {
  low: 'bg-green-100 text-green-800',
  medium: 'bg-blue-100 text-blue-800',
  high: 'bg-orange-100 text-orange-800',
  urgent: 'bg-red-100 text-red-800',
};

const statusColors = {
  todo: 'bg-gray-100 text-gray-800',
  in_progress: 'bg-amber-100 text-amber-800',
  done: 'bg-green-100 text-green-800',
  cancelled: 'bg-violet-100 text-violet-800',
};

export function TaskDetailModal({
  open,
  onOpenChange,
  event,
  onSuccess,
  onEdit,
}: TaskDetailModalProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState('');

  // Calendar operations
  const { updateStatus, deleteTask } = useCalendarOperations();

  const task = event?.resource;

  const handleStatusChange = async (newStatus: TaskStatus) => {
    if (!task) return;

    try {
      setError('');
      await updateStatus.mutateAsync({ taskId: task.id, status: newStatus });
      onSuccess?.();
    } catch (err: any) {
      setError(err.message || 'Failed to update task status');
    }
  };

  const handleDelete = async () => {
    if (!task) return;

    try {
      setError('');
      setIsDeleting(true);
      await deleteTask.mutateAsync(task.id);
      onSuccess?.();
      onOpenChange(false);
    } catch (err: any) {
      setError(err.message || 'Failed to delete task');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleEdit = () => {
    if (event && onEdit) {
      onEdit(event);
    }
    onOpenChange(false);
  };

  if (!event || !task) return null;

  const formatDateTime = (date: Date) => {
    return format(date, "EEEE, MMMM d, yyyy 'at' h:mm a");
  };

  const formatDateOnly = (date: Date) => {
    return format(date, 'EEEE, MMMM d, yyyy');
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1 pr-4">
              <DialogTitle className="text-lg leading-tight">{event.title}</DialogTitle>
              <DialogDescription className="mt-1">Task Details</DialogDescription>
            </div>

            {/* Actions Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                  <MoreVertical className="h-4 w-4" />
                  <span className="sr-only">Open menu</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                {onEdit && (
                  <DropdownMenuItem onClick={handleEdit}>
                    <Edit className="mr-2 h-4 w-4" />
                    Edit Task
                  </DropdownMenuItem>
                )}

                <DropdownMenuSeparator />

                {statusChangeOptions
                  .filter((option) => option.value !== task.status)
                  .map((option) => {
                    const Icon = option.icon;
                    return (
                      <DropdownMenuItem
                        key={option.value}
                        onClick={() => handleStatusChange(option.value)}
                        disabled={updateStatus.isPending}
                      >
                        <Icon className={cn('mr-2 h-4 w-4', option.color)} />
                        {option.label}
                      </DropdownMenuItem>
                    );
                  })}

                <DropdownMenuSeparator />

                <DropdownMenuItem
                  onClick={handleDelete}
                  disabled={isDeleting}
                  className="text-red-600 focus:text-red-600"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  {isDeleting ? 'Deleting...' : 'Delete Task'}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </DialogHeader>

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="space-y-6">
          {/* Task Description */}
          {task.description && (
            <div>
              <h4 className="text-sm font-medium text-muted-foreground mb-2">Description</h4>
              <p className="text-sm leading-relaxed bg-muted p-3 rounded-lg">{task.description}</p>
            </div>
          )}

          {/* Status and Priority */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4 className="text-sm font-medium text-muted-foreground mb-2">Status</h4>
              <Badge className={cn('capitalize', statusColors[task.status])} variant="secondary">
                {task.status.replace('_', ' ')}
              </Badge>
            </div>

            <div>
              <h4 className="text-sm font-medium text-muted-foreground mb-2">Priority</h4>
              <Badge
                className={cn('capitalize', priorityColors[task.priority])}
                variant="secondary"
              >
                {task.priority === 'urgent' && <AlertTriangle className="mr-1 h-3 w-3" />}
                {task.priority}
              </Badge>
            </div>
          </div>

          {/* Timing Information */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-muted-foreground">Timing</h4>

            <div className="space-y-2 text-sm">
              {event.allDay ? (
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span>All day on {formatDateOnly(event.end)}</span>
                </div>
              ) : (
                <>
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span>From: {formatDateTime(event.start)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span>To: {formatDateTime(event.end)}</span>
                  </div>
                </>
              )}

              {task.estimated_hours && (
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span>Estimated: {task.estimated_hours} hours</span>
                </div>
              )}

              {task.actual_hours && (
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  <span>Actual: {task.actual_hours} hours</span>
                </div>
              )}
            </div>
          </div>

          {/* Project and Assignment */}
          <div className="space-y-3">
            {task.project && (
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">Project</h4>
                <div className="flex items-center gap-2 text-sm">
                  <FolderOpen className="h-4 w-4 text-muted-foreground" />
                  <span>{task.project.name}</span>
                </div>
              </div>
            )}

            {task.assigned_to && (
              <div>
                <h4 className="text-sm font-medium text-muted-foreground mb-2">Assigned To</h4>
                <div className="flex items-center gap-2 text-sm">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <span>{task.assigned_to.full_name || task.assigned_to.username}</span>
                </div>
              </div>
            )}
          </div>

          {/* Tags */}
          {task.tags && task.tags.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-muted-foreground mb-2">Tags</h4>
              <div className="flex flex-wrap gap-2">
                {task.tags.map((tag) => (
                  <Badge
                    key={tag.id}
                    variant="outline"
                    className="text-xs"
                    style={{
                      borderColor: tag.color,
                      color: tag.color,
                    }}
                  >
                    <Tag className="mr-1 h-3 w-3" />
                    {tag.name}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Metadata */}
          <div className="pt-4 border-t text-xs text-muted-foreground space-y-1">
            <div>Created: {format(new Date(task.created_at), 'PPp')}</div>
            <div>Updated: {format(new Date(task.updated_at), 'PPp')}</div>
            {task.completed_at && (
              <div>Completed: {format(new Date(task.completed_at), 'PPp')}</div>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={updateStatus.isPending || isDeleting}
          >
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default TaskDetailModal;
