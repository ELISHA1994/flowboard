import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  RemindersService,
  TaskReminder,
  TaskReminderCreate,
  TaskReminderUpdate,
  TaskDueDateRemindersCreate,
  NotificationPreferences,
  NotificationPreferencesUpdate,
} from '@/lib/api/reminders';
import { useToastContext } from '@/contexts/toast-context';

// Query keys for cache management
export const reminderKeys = {
  all: ['reminders'] as const,
  task: (taskId: string) => [...reminderKeys.all, 'task', taskId] as const,
  preferences: () => ['notification-preferences'] as const,
};

// Hook for fetching reminders for a specific task
export function useTaskReminders(taskId: string) {
  return useQuery({
    queryKey: reminderKeys.task(taskId),
    queryFn: () => RemindersService.getTaskReminders(taskId),
    enabled: !!taskId,
    staleTime: 30 * 1000, // 30 seconds
  });
}

// Hook for fetching notification preferences
export function useNotificationPreferences() {
  return useQuery({
    queryKey: reminderKeys.preferences(),
    queryFn: () => RemindersService.getNotificationPreferences(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Hook for creating a custom task reminder
export function useCreateReminderMutation() {
  const queryClient = useQueryClient();
  const { toast } = useToastContext();

  return useMutation({
    mutationFn: (reminder: TaskReminderCreate) => RemindersService.createTaskReminder(reminder),
    onSuccess: (newReminder) => {
      // Invalidate the task reminders cache
      queryClient.invalidateQueries({ queryKey: reminderKeys.task(newReminder.task_id) });

      toast({
        title: 'Reminder created',
        description: 'Your task reminder has been set successfully',
      });
    },
    onError: (error) => {
      toast({
        title: 'Error creating reminder',
        description: error instanceof Error ? error.message : 'Failed to create reminder',
        variant: 'destructive',
      });
    },
  });
}

// Hook for creating due date reminders
export function useCreateDueDateRemindersMutation() {
  const queryClient = useQueryClient();
  const { toast } = useToastContext();

  return useMutation({
    mutationFn: (data: TaskDueDateRemindersCreate) => RemindersService.createDueDateReminders(data),
    onSuccess: (reminders) => {
      if (reminders.length > 0) {
        // Invalidate the task reminders cache
        queryClient.invalidateQueries({ queryKey: reminderKeys.task(reminders[0].task_id) });

        toast({
          title: 'Due date reminders created',
          description: `Created ${reminders.length} reminder${reminders.length > 1 ? 's' : ''} for this task`,
        });
      }
    },
    onError: (error) => {
      toast({
        title: 'Error creating due date reminders',
        description: error instanceof Error ? error.message : 'Failed to create due date reminders',
        variant: 'destructive',
      });
    },
  });
}

// Hook for updating a task reminder
export function useUpdateReminderMutation() {
  const queryClient = useQueryClient();
  const { toast } = useToastContext();

  return useMutation({
    mutationFn: ({ reminderId, update }: { reminderId: string; update: TaskReminderUpdate }) =>
      RemindersService.updateTaskReminder(reminderId, update),
    onMutate: async ({ reminderId, update }) => {
      // Find which task this reminder belongs to by searching through cached reminders
      const queryCache = queryClient.getQueryCache();
      let taskId: string | null = null;

      queryCache.getAll().forEach((query) => {
        if (query.queryKey[0] === 'reminders' && query.queryKey[1] === 'task') {
          const reminders = query.state.data as TaskReminder[] | undefined;
          if (reminders?.some((r) => r.id === reminderId)) {
            taskId = query.queryKey[2] as string;
          }
        }
      });

      if (taskId) {
        // Cancel any outgoing refetches
        await queryClient.cancelQueries({ queryKey: reminderKeys.task(taskId) });

        // Snapshot the previous value
        const previousReminders = queryClient.getQueryData(reminderKeys.task(taskId));

        // Optimistically update the reminder
        queryClient.setQueryData(reminderKeys.task(taskId), (old: TaskReminder[] | undefined) => {
          if (!old) return old;
          return old.map((reminder) =>
            reminder.id === reminderId ? { ...reminder, ...update } : reminder
          );
        });

        // Return a context object with the snapshotted value
        return { previousReminders, taskId };
      }

      return { previousReminders: null, taskId: null };
    },
    onError: (error, { reminderId }, context) => {
      // If the mutation fails, use the context returned from onMutate to roll back
      if (context?.previousReminders && context.taskId) {
        queryClient.setQueryData(reminderKeys.task(context.taskId), context.previousReminders);
      }

      toast({
        title: 'Error updating reminder',
        description: error instanceof Error ? error.message : 'Failed to update reminder',
        variant: 'destructive',
      });
    },
    onSuccess: (updatedReminder, { reminderId }) => {
      // Invalidate and refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: reminderKeys.task(updatedReminder.task_id) });

      toast({
        title: 'Reminder updated',
        description: 'Your reminder has been updated successfully',
      });
    },
  });
}

// Hook for deleting a task reminder
export function useDeleteReminderMutation() {
  const queryClient = useQueryClient();
  const { toast } = useToastContext();

  return useMutation({
    mutationFn: (reminderId: string) => RemindersService.deleteTaskReminder(reminderId),
    onMutate: async (reminderId) => {
      // Find which task this reminder belongs to
      const queryCache = queryClient.getQueryCache();
      let taskId: string | null = null;
      let reminderToDelete: TaskReminder | null = null;

      queryCache.getAll().forEach((query) => {
        if (query.queryKey[0] === 'reminders' && query.queryKey[1] === 'task') {
          const reminders = query.state.data as TaskReminder[] | undefined;
          const foundReminder = reminders?.find((r) => r.id === reminderId);
          if (foundReminder) {
            taskId = query.queryKey[2] as string;
            reminderToDelete = foundReminder;
          }
        }
      });

      if (taskId) {
        // Cancel any outgoing refetches
        await queryClient.cancelQueries({ queryKey: reminderKeys.task(taskId) });

        // Snapshot the previous value
        const previousReminders = queryClient.getQueryData(reminderKeys.task(taskId));

        // Optimistically remove the reminder
        queryClient.setQueryData(reminderKeys.task(taskId), (old: TaskReminder[] | undefined) => {
          if (!old) return old;
          return old.filter((reminder) => reminder.id !== reminderId);
        });

        return { previousReminders, taskId, reminderToDelete };
      }

      return { previousReminders: null, taskId: null, reminderToDelete: null };
    },
    onError: (error, reminderId, context) => {
      // Roll back on error
      if (context?.previousReminders && context.taskId) {
        queryClient.setQueryData(reminderKeys.task(context.taskId), context.previousReminders);
      }

      toast({
        title: 'Error deleting reminder',
        description: error instanceof Error ? error.message : 'Failed to delete reminder',
        variant: 'destructive',
      });
    },
    onSuccess: (_, reminderId, context) => {
      if (context?.taskId) {
        // Invalidate queries to ensure consistency
        queryClient.invalidateQueries({ queryKey: reminderKeys.task(context.taskId) });
      }

      toast({
        title: 'Reminder deleted',
        description: 'The reminder has been removed successfully',
      });
    },
  });
}

// Hook for updating notification preferences
export function useUpdateNotificationPreferencesMutation() {
  const queryClient = useQueryClient();
  const { toast } = useToastContext();

  return useMutation({
    mutationFn: (preferences: NotificationPreferencesUpdate) =>
      RemindersService.updateNotificationPreferences(preferences),
    onMutate: async (newPreferences) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: reminderKeys.preferences() });

      // Snapshot the previous value
      const previousPreferences = queryClient.getQueryData(reminderKeys.preferences());

      // Optimistically update the preferences
      queryClient.setQueryData(
        reminderKeys.preferences(),
        (old: NotificationPreferences | undefined) => {
          if (!old) return old;
          return { ...old, ...newPreferences };
        }
      );

      // Return a context object with the snapshotted value
      return { previousPreferences };
    },
    onError: (error, newPreferences, context) => {
      // If the mutation fails, use the context returned from onMutate to roll back
      if (context?.previousPreferences) {
        queryClient.setQueryData(reminderKeys.preferences(), context.previousPreferences);
      }

      toast({
        title: 'Error updating preferences',
        description:
          error instanceof Error ? error.message : 'Failed to update notification preferences',
        variant: 'destructive',
      });
    },
    onSuccess: (updatedPreferences) => {
      // Invalidate and refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: reminderKeys.preferences() });

      toast({
        title: 'Preferences updated',
        description: 'Your notification preferences have been saved',
      });
    },
  });
}

// Hook for manually processing reminders (for testing/admin)
export function useProcessRemindersMutation() {
  const { toast } = useToastContext();

  return useMutation({
    mutationFn: () => RemindersService.processReminders(),
    onSuccess: () => {
      toast({
        title: 'Reminders processed',
        description: 'All pending reminders have been processed',
      });
    },
    onError: (error) => {
      toast({
        title: 'Error processing reminders',
        description: error instanceof Error ? error.message : 'Failed to process reminders',
        variant: 'destructive',
      });
    },
  });
}
