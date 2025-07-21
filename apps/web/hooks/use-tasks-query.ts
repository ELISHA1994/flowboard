import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { TasksService, Task, TaskStatistics, CreateTaskDto, UpdateTaskDto } from '@/lib/api/tasks';
import { useToastContext } from '@/contexts/toast-context';

// Query keys for cache management
export const taskKeys = {
  all: ['tasks'] as const,
  lists: () => [...taskKeys.all, 'list'] as const,
  list: (params?: Parameters<typeof TasksService.getTasks>[0]) =>
    [...taskKeys.lists(), params] as const,
  details: () => [...taskKeys.all, 'detail'] as const,
  detail: (id: string) => [...taskKeys.details(), id] as const,
  statistics: (params?: Parameters<typeof TasksService.getStatistics>[0]) =>
    ['taskStatistics', params] as const,
  recent: (limit: number) => ['recentTasks', limit] as const,
  upcoming: (days: number) => ['upcomingTasks', days] as const,
};

// Hook for fetching tasks with automatic caching
export function useTasksQuery(params?: Parameters<typeof TasksService.getTasks>[0]) {
  return useQuery({
    queryKey: taskKeys.list(params),
    queryFn: () => TasksService.getTasks(params),
    staleTime: 30 * 1000, // 30 seconds
  });
}

// Hook for fetching a single task
export function useTaskQuery(id: string) {
  return useQuery({
    queryKey: taskKeys.detail(id),
    queryFn: () => TasksService.getTask(id),
    enabled: !!id,
  });
}

// Hook for fetching task statistics
export function useTaskStatisticsQuery(params?: Parameters<typeof TasksService.getStatistics>[0]) {
  return useQuery({
    queryKey: taskKeys.statistics(params),
    queryFn: () => TasksService.getStatistics(params),
    staleTime: 60 * 1000, // 1 minute
  });
}

// Hook for fetching recent tasks
export function useRecentTasksQuery(limit: number = 5) {
  return useQuery({
    queryKey: taskKeys.recent(limit),
    queryFn: () => TasksService.getRecentTasks(limit),
    staleTime: 30 * 1000, // 30 seconds
  });
}

// Hook for fetching upcoming tasks
export function useUpcomingTasksQuery(days: number = 7) {
  return useQuery({
    queryKey: taskKeys.upcoming(days),
    queryFn: () => TasksService.getUpcomingTasks(days),
    staleTime: 60 * 1000, // 1 minute
  });
}

// Hook for creating a task with optimistic updates
export function useCreateTaskMutation() {
  const queryClient = useQueryClient();
  const { toast } = useToastContext();

  return useMutation({
    mutationFn: (data: CreateTaskDto) => TasksService.createTask(data),
    onMutate: async (newTask) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: taskKeys.lists() });

      // Snapshot the previous value
      const previousTasks = queryClient.getQueryData(taskKeys.list());

      // Optimistically update to the new value
      queryClient.setQueryData(taskKeys.list(), (old: any) => {
        if (!old) return old;
        return {
          ...old,
          tasks: [
            {
              ...newTask,
              id: `temp-${Date.now()}`,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
              time_tracked: 0,
              owner_id: 'temp',
              owner: { id: 'temp', username: 'You', email: '' },
              project: null,
              assigned_to: null,
              tags: [],
              attachments: [],
              shared_with: [],
              comments_count: 0,
              is_shared: false,
              shared_with_me: false,
              has_unread_activity: false,
            },
            ...(old.tasks || []),
          ],
          total: (old.total || 0) + 1,
        };
      });

      // Return a context object with the snapshotted value
      return { previousTasks };
    },
    onError: (err, newTask, context) => {
      // If the mutation fails, use the context returned from onMutate to roll back
      if (context?.previousTasks) {
        queryClient.setQueryData(taskKeys.list(), context.previousTasks);
      }
      toast({
        title: 'Error creating task',
        description: err instanceof Error ? err.message : 'Failed to create task',
        variant: 'destructive',
      });
    },
    onSuccess: (data) => {
      // Invalidate and refetch all task-related queries
      queryClient.invalidateQueries({ queryKey: taskKeys.all });
      queryClient.invalidateQueries({ queryKey: taskKeys.statistics() });
      queryClient.invalidateQueries({ queryKey: taskKeys.recent(5) });
      queryClient.invalidateQueries({ queryKey: taskKeys.upcoming(7) });

      toast({
        title: 'Task created',
        description: 'Your task has been created successfully',
      });
    },
  });
}

// Hook for updating a task
export function useUpdateTaskMutation() {
  const queryClient = useQueryClient();
  const { toast } = useToastContext();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateTaskDto }) =>
      TasksService.updateTask(id, data),
    onMutate: async ({ id, data }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: taskKeys.detail(id) });
      await queryClient.cancelQueries({ queryKey: taskKeys.lists() });

      // Snapshot the previous values
      const previousTask = queryClient.getQueryData(taskKeys.detail(id));
      const previousTasks = queryClient.getQueryData(taskKeys.list());

      // Optimistically update the task
      queryClient.setQueryData(taskKeys.detail(id), (old: any) => ({
        ...old,
        ...data,
        updated_at: new Date().toISOString(),
      }));

      // Update in lists too
      queryClient.setQueriesData({ queryKey: taskKeys.lists() }, (old: any) => {
        if (!old || !old.tasks) return old;
        return {
          ...old,
          tasks: old.tasks.map((task: Task) =>
            task.id === id ? { ...task, ...data, updated_at: new Date().toISOString() } : task
          ),
        };
      });

      return { previousTask, previousTasks };
    },
    onError: (err, variables, context) => {
      // Roll back on error
      if (context?.previousTask) {
        queryClient.setQueryData(taskKeys.detail(variables.id), context.previousTask);
      }
      if (context?.previousTasks) {
        queryClient.setQueryData(taskKeys.list(), context.previousTasks);
      }
      toast({
        title: 'Error updating task',
        description: err instanceof Error ? err.message : 'Failed to update task',
        variant: 'destructive',
      });
    },
    onSuccess: (data, variables) => {
      // Invalidate queries to ensure consistency
      queryClient.invalidateQueries({ queryKey: taskKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
      queryClient.invalidateQueries({ queryKey: taskKeys.statistics() });

      toast({
        title: 'Task updated',
        description: 'Your changes have been saved',
      });
    },
  });
}

// Hook for deleting a task
export function useDeleteTaskMutation() {
  const queryClient = useQueryClient();
  const { toast } = useToastContext();

  return useMutation({
    mutationFn: (id: string) => TasksService.deleteTask(id),
    onMutate: async (id) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: taskKeys.lists() });

      // Snapshot the previous value
      const previousTasks = queryClient.getQueryData(taskKeys.list());

      // Optimistically remove the task
      queryClient.setQueriesData({ queryKey: taskKeys.lists() }, (old: any) => {
        if (!old || !old.tasks) return old;
        return {
          ...old,
          tasks: old.tasks.filter((task: Task) => task.id !== id),
          total: Math.max(0, (old.total || 0) - 1),
        };
      });

      return { previousTasks };
    },
    onError: (err, id, context) => {
      // Roll back on error
      if (context?.previousTasks) {
        queryClient.setQueryData(taskKeys.list(), context.previousTasks);
      }
      toast({
        title: 'Error deleting task',
        description: err instanceof Error ? err.message : 'Failed to delete task',
        variant: 'destructive',
      });
    },
    onSuccess: () => {
      // Invalidate all task-related queries
      queryClient.invalidateQueries({ queryKey: taskKeys.all });
      queryClient.invalidateQueries({ queryKey: taskKeys.statistics() });
      queryClient.invalidateQueries({ queryKey: taskKeys.recent(5) });
      queryClient.invalidateQueries({ queryKey: taskKeys.upcoming(7) });

      toast({
        title: 'Task deleted',
        description: 'The task has been removed',
      });
    },
  });
}

// Hook for bulk updating tasks
export function useBulkUpdateTasksMutation() {
  const queryClient = useQueryClient();
  const { toast } = useToastContext();

  return useMutation({
    mutationFn: ({ ids, data }: { ids: string[]; data: UpdateTaskDto }) =>
      TasksService.bulkUpdateTasks(ids, data),
    onSuccess: () => {
      // Invalidate all task queries to ensure consistency
      queryClient.invalidateQueries({ queryKey: taskKeys.all });
      queryClient.invalidateQueries({ queryKey: taskKeys.statistics() });

      toast({
        title: 'Tasks updated',
        description: 'All selected tasks have been updated',
      });
    },
    onError: (err) => {
      toast({
        title: 'Error updating tasks',
        description: err instanceof Error ? err.message : 'Failed to update tasks',
        variant: 'destructive',
      });
    },
  });
}

// Hook for bulk deleting tasks
export function useBulkDeleteTasksMutation() {
  const queryClient = useQueryClient();
  const { toast } = useToastContext();

  return useMutation({
    mutationFn: (ids: string[]) => TasksService.bulkDeleteTasks(ids),
    onSuccess: () => {
      // Invalidate all task queries
      queryClient.invalidateQueries({ queryKey: taskKeys.all });
      queryClient.invalidateQueries({ queryKey: taskKeys.statistics() });
      queryClient.invalidateQueries({ queryKey: taskKeys.recent(5) });
      queryClient.invalidateQueries({ queryKey: taskKeys.upcoming(7) });

      toast({
        title: 'Tasks deleted',
        description: 'All selected tasks have been removed',
      });
    },
    onError: (err) => {
      toast({
        title: 'Error deleting tasks',
        description: err instanceof Error ? err.message : 'Failed to delete tasks',
        variant: 'destructive',
      });
    },
  });
}
