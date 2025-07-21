import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { TasksService, Task, CreateTaskRequest, UpdateTaskRequest } from '@/lib/api/tasks';
import { AuthService } from '@/lib/auth';
import { useToastContext } from '@/contexts/toast-context';

// Import taskKeys from existing tasks query hook
const taskKeys = {
  all: ['tasks'] as const,
  lists: () => [...taskKeys.all, 'list'] as const,
  list: (filters: string) => [...taskKeys.lists(), { filters }] as const,
  details: () => [...taskKeys.all, 'detail'] as const,
  detail: (id: string) => [...taskKeys.details(), id] as const,
  statistics: () => [...taskKeys.all, 'statistics'] as const,
};

// Subtask-specific query keys
export const subtaskKeys = {
  all: ['subtasks'] as const,
  lists: () => [...subtaskKeys.all, 'list'] as const,
  list: (parentTaskId: string) => [...subtaskKeys.lists(), parentTaskId] as const,
};

// Enhanced API service for subtasks
const SubtasksAPI = {
  async getSubtasks(parentTaskId: string): Promise<Task[]> {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const response = await fetch(`${API_BASE_URL}/tasks/${parentTaskId}/subtasks`, {
      headers: {
        Authorization: `Bearer ${AuthService.getToken()}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to fetch subtasks' }));
      throw new Error(error.detail || `Failed to fetch subtasks: ${response.status}`);
    }

    return response.json();
  },
};

// Hook for fetching subtasks with dependent query pattern
export function useSubtasksQuery(parentTaskId: string) {
  return useQuery({
    queryKey: subtaskKeys.list(parentTaskId),
    queryFn: () => SubtasksAPI.getSubtasks(parentTaskId),
    enabled: !!parentTaskId, // Dependent query - only run when parent task ID exists
    staleTime: 30 * 1000, // 30 seconds
    // Retry with exponential backoff
    retry: (failureCount, error) => {
      // Don't retry on 404 (task not found) or 403 (permission denied)
      if (error instanceof Error && error.message.includes('404')) return false;
      if (error instanceof Error && error.message.includes('403')) return false;
      return failureCount < 3;
    },
    // Placeholder data to prevent loading states
    placeholderData: [],
  });
}

// Hook for creating subtasks with optimistic updates
export function useCreateSubtaskMutation(parentTaskId: string) {
  const queryClient = useQueryClient();
  const { toast } = useToastContext();

  return useMutation({
    mutationFn: (data: CreateTaskRequest) =>
      TasksService.createTask({ ...data, parent_task_id: parentTaskId }),

    // Optimistic update using cache manipulation
    onMutate: async (newSubtask) => {
      const subtaskQueryKey = subtaskKeys.list(parentTaskId);
      const parentTaskQueryKey = taskKeys.detail(parentTaskId);

      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: subtaskQueryKey });
      await queryClient.cancelQueries({ queryKey: parentTaskQueryKey });

      // Snapshot the previous values
      const previousSubtasks = queryClient.getQueryData(subtaskQueryKey);
      const previousParentTask = queryClient.getQueryData(parentTaskQueryKey);

      // Optimistically update subtasks list
      queryClient.setQueryData(subtaskQueryKey, (old: Task[] = []) => [
        {
          ...newSubtask,
          id: `temp-${Date.now()}`,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          user_id: 'temp',
          parent_task_id: parentTaskId,
          tags: [],
          categories: [],
          dependencies: [],
          dependents: [],
          subtasks: [],
        } as Task,
        ...old,
      ]);

      // Optimistically update parent task to reflect new subtask count
      queryClient.setQueryData(parentTaskQueryKey, (old: Task | undefined) => {
        if (!old) return old;
        return {
          ...old,
          subtasks: [...(old.subtasks || []), { id: `temp-${Date.now()}` }],
        };
      });

      return { previousSubtasks, previousParentTask };
    },

    onError: (err, newSubtask, context) => {
      // Rollback optimistic updates
      if (context?.previousSubtasks) {
        queryClient.setQueryData(subtaskKeys.list(parentTaskId), context.previousSubtasks);
      }
      if (context?.previousParentTask) {
        queryClient.setQueryData(taskKeys.detail(parentTaskId), context.previousParentTask);
      }

      toast({
        title: 'Error creating subtask',
        description: err instanceof Error ? err.message : 'Failed to create subtask',
        variant: 'destructive',
      });
    },

    onSuccess: (data) => {
      // Invalidate related queries to ensure consistency
      queryClient.invalidateQueries({ queryKey: subtaskKeys.list(parentTaskId) });
      queryClient.invalidateQueries({ queryKey: taskKeys.detail(parentTaskId) });
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
      queryClient.invalidateQueries({ queryKey: taskKeys.statistics() });

      toast({
        title: 'Subtask created',
        description: 'Your subtask has been created successfully',
      });
    },
  });
}

// Hook for updating subtasks with optimistic updates
export function useUpdateSubtaskMutation(parentTaskId: string) {
  const queryClient = useQueryClient();
  const { toast } = useToastContext();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateTaskRequest }) =>
      TasksService.updateTask(id, data),

    onMutate: async ({ id, data }) => {
      const subtaskQueryKey = subtaskKeys.list(parentTaskId);
      const taskQueryKey = taskKeys.detail(id);

      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: subtaskQueryKey });
      await queryClient.cancelQueries({ queryKey: taskQueryKey });

      // Snapshot previous values
      const previousSubtasks = queryClient.getQueryData(subtaskQueryKey);
      const previousTask = queryClient.getQueryData(taskQueryKey);

      // Optimistically update subtasks list
      queryClient.setQueryData(subtaskQueryKey, (old: Task[] = []) =>
        old.map((subtask) =>
          subtask.id === id
            ? { ...subtask, ...data, updated_at: new Date().toISOString() }
            : subtask
        )
      );

      // Optimistically update individual task cache
      queryClient.setQueryData(taskQueryKey, (old: Task | undefined) => {
        if (!old) return old;
        return { ...old, ...data, updated_at: new Date().toISOString() };
      });

      return { previousSubtasks, previousTask };
    },

    onError: (err, variables, context) => {
      // Rollback on error
      if (context?.previousSubtasks) {
        queryClient.setQueryData(subtaskKeys.list(parentTaskId), context.previousSubtasks);
      }
      if (context?.previousTask) {
        queryClient.setQueryData(taskKeys.detail(variables.id), context.previousTask);
      }

      toast({
        title: 'Error updating subtask',
        description: err instanceof Error ? err.message : 'Failed to update subtask',
        variant: 'destructive',
      });
    },

    onSuccess: (data, variables) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: subtaskKeys.list(parentTaskId) });
      queryClient.invalidateQueries({ queryKey: taskKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: taskKeys.detail(parentTaskId) });

      toast({
        title: 'Subtask updated',
        description: 'Your changes have been saved',
      });
    },
  });
}

// Hook for deleting subtasks with optimistic updates
export function useDeleteSubtaskMutation(parentTaskId: string) {
  const queryClient = useQueryClient();
  const { toast } = useToastContext();

  return useMutation({
    mutationFn: (id: string) => TasksService.deleteTask(id),

    onMutate: async (id) => {
      const subtaskQueryKey = subtaskKeys.list(parentTaskId);
      const parentTaskQueryKey = taskKeys.detail(parentTaskId);

      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: subtaskQueryKey });
      await queryClient.cancelQueries({ queryKey: parentTaskQueryKey });

      // Snapshot previous values
      const previousSubtasks = queryClient.getQueryData(subtaskQueryKey);
      const previousParentTask = queryClient.getQueryData(parentTaskQueryKey);

      // Optimistically remove subtask
      queryClient.setQueryData(subtaskQueryKey, (old: Task[] = []) =>
        old.filter((subtask) => subtask.id !== id)
      );

      // Update parent task subtasks count
      queryClient.setQueryData(parentTaskQueryKey, (old: Task | undefined) => {
        if (!old) return old;
        return {
          ...old,
          subtasks: (old.subtasks || []).filter((st: any) => st.id !== id),
        };
      });

      return { previousSubtasks, previousParentTask };
    },

    onError: (err, id, context) => {
      // Rollback on error
      if (context?.previousSubtasks) {
        queryClient.setQueryData(subtaskKeys.list(parentTaskId), context.previousSubtasks);
      }
      if (context?.previousParentTask) {
        queryClient.setQueryData(taskKeys.detail(parentTaskId), context.previousParentTask);
      }

      toast({
        title: 'Error deleting subtask',
        description: err instanceof Error ? err.message : 'Failed to delete subtask',
        variant: 'destructive',
      });
    },

    onSuccess: () => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: subtaskKeys.list(parentTaskId) });
      queryClient.invalidateQueries({ queryKey: taskKeys.detail(parentTaskId) });
      queryClient.invalidateQueries({ queryKey: taskKeys.lists() });
      queryClient.invalidateQueries({ queryKey: taskKeys.statistics() });

      toast({
        title: 'Subtask deleted',
        description: 'The subtask has been removed',
      });
    },
  });
}
