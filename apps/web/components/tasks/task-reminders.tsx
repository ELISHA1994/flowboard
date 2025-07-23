'use client';

import React, { useState } from 'react';
import { format, isAfter, isBefore } from 'date-fns';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Bell,
  BellRing,
  Calendar,
  Clock,
  Edit2,
  MoreVertical,
  Plus,
  Trash2,
  AlertCircle,
} from 'lucide-react';
import { useTaskReminders, useDeleteReminderMutation } from '@/hooks/use-reminders';
import { TaskReminder } from '@/lib/api/reminders';
import { Task } from '@/lib/api/tasks';
import { CreateReminderModal } from './create-reminder-modal';
import { cn } from '@/lib/utils';

interface TaskRemindersProps {
  task: Task;
  className?: string;
}

export function TaskReminders({ task, className }: TaskRemindersProps) {
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editingReminder, setEditingReminder] = useState<TaskReminder | null>(null);

  const { data: reminders = [], isLoading, error } = useTaskReminders(task.id);
  const deleteReminderMutation = useDeleteReminderMutation();

  const handleDeleteReminder = async (reminderId: string) => {
    await deleteReminderMutation.mutateAsync(reminderId);
  };

  const handleEditReminder = (reminder: TaskReminder) => {
    setEditingReminder(reminder);
    setCreateModalOpen(true);
  };

  const handleCreateComplete = () => {
    setCreateModalOpen(false);
    setEditingReminder(null);
  };

  const formatReminderTime = (remindAt: string) => {
    const reminderDate = new Date(remindAt);
    const now = new Date();

    if (isBefore(reminderDate, now)) {
      return `${format(reminderDate, 'MMM d, yyyy h:mm a')} (Overdue)`;
    }

    return format(reminderDate, 'MMM d, yyyy h:mm a');
  };

  const getReminderStatus = (reminder: TaskReminder) => {
    const now = new Date();
    const reminderTime = new Date(reminder.remind_at);

    if (reminder.sent) {
      return { status: 'sent', color: 'bg-gray-100 text-gray-700' };
    } else if (isBefore(reminderTime, now)) {
      return { status: 'overdue', color: 'bg-red-100 text-red-700' };
    } else {
      return { status: 'pending', color: 'bg-blue-100 text-blue-700' };
    }
  };

  const getStatusIcon = (reminder: TaskReminder) => {
    const { status } = getReminderStatus(reminder);

    switch (status) {
      case 'sent':
        return <BellRing className="h-4 w-4" />;
      case 'overdue':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <Bell className="h-4 w-4" />;
    }
  };

  if (error) {
    return (
      <div className={cn('rounded-lg border bg-card text-card-foreground shadow-sm', className)}>
        <div className="p-4">
          <div className="flex items-center gap-2 text-red-600">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">Failed to load reminders</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className={cn('rounded-lg border bg-card text-card-foreground shadow-sm', className)}>
        <div className="flex flex-col space-y-1.5 p-4 pb-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium flex items-center gap-2">
              <Bell className="h-4 w-4" />
              Reminders
            </h3>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setCreateModalOpen(true)}
              className="h-8 px-2"
            >
              <Plus className="h-4 w-4 mr-1" />
              Add
            </Button>
          </div>
        </div>
        <div className="p-4 pt-0">
          {isLoading ? (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Clock className="h-4 w-4 animate-spin" />
              <span className="text-sm">Loading reminders...</span>
            </div>
          ) : reminders.length === 0 ? (
            <div className="text-center py-6">
              <Bell className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
              <p className="text-sm text-muted-foreground mb-3">No reminders set</p>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setCreateModalOpen(true)}
              >
                <Plus className="h-4 w-4 mr-1" />
                Add Reminder
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {reminders.map((reminder) => {
                const { status, color } = getReminderStatus(reminder);

                return (
                  <div
                    key={reminder.id}
                    className="flex items-start gap-3 p-3 rounded-lg border bg-gray-50/50"
                  >
                    <div className="flex-shrink-0 mt-0.5">{getStatusIcon(reminder)}</div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant="secondary" className={cn('text-xs', color)}>
                              {status.charAt(0).toUpperCase() + status.slice(1)}
                            </Badge>
                            <Badge variant="outline" className="text-xs">
                              {reminder.reminder_type === 'due_date' ? (
                                <Calendar className="h-3 w-3 mr-1" />
                              ) : (
                                <Clock className="h-3 w-3 mr-1" />
                              )}
                              {reminder.reminder_type === 'due_date' ? 'Due Date' : 'Custom'}
                            </Badge>
                          </div>

                          <p className="text-sm font-medium text-gray-900 mb-1">
                            {formatReminderTime(reminder.remind_at)}
                          </p>

                          {reminder.message && (
                            <p className="text-sm text-muted-foreground">{reminder.message}</p>
                          )}

                          {reminder.reminder_type === 'due_date' && reminder.offset_minutes && (
                            <p className="text-xs text-muted-foreground mt-1">
                              {reminder.offset_minutes >= 1440
                                ? `${Math.floor(reminder.offset_minutes / 1440)} day(s) before due date`
                                : reminder.offset_minutes >= 60
                                  ? `${Math.floor(reminder.offset_minutes / 60)} hour(s) before due date`
                                  : `${reminder.offset_minutes} minute(s) before due date`}
                            </p>
                          )}
                        </div>

                        {!reminder.sent && (
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                className="h-8 w-8 p-0"
                              >
                                <MoreVertical className="h-4 w-4" />
                                <span className="sr-only">Open menu</span>
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => handleEditReminder(reminder)}>
                                <Edit2 className="h-4 w-4 mr-2" />
                                Edit
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                onClick={() => handleDeleteReminder(reminder.id)}
                                className="text-red-600 focus:text-red-600"
                                disabled={deleteReminderMutation.isPending}
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      <CreateReminderModal
        task={task}
        reminder={editingReminder}
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
        onComplete={handleCreateComplete}
      />
    </>
  );
}
