import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { TasksService, Task, TaskStatus } from '@/lib/api/tasks';
import {
  CalendarEvent,
  tasksToCalendarEvents,
  getCalendarDateRange,
} from '@/lib/calendar/calendar-utils';
import { format } from 'date-fns';

export interface CalendarFilters {
  project_id?: string;
  assigned_to_id?: string;
  status?: TaskStatus[];
  priority?: string[];
  show_completed?: boolean;
}

/**
 * Hook to fetch tasks for calendar display
 */
export function useCalendarTasks(date: Date, view: string, filters?: CalendarFilters) {
  const { start, end } = getCalendarDateRange(date, view);

  return useQuery({
    queryKey: ['calendar-tasks', format(start, 'yyyy-MM-dd'), format(end, 'yyyy-MM-dd'), filters],
    queryFn: async () => {
      // Use backend date range filtering
      const response = await TasksService.getTasks({
        project_id: filters?.project_id,
        assigned_to_id: filters?.assigned_to_id,
        // For now, only filter by the first status/priority if multiple are selected
        status: filters?.status?.[0],
        priority: filters?.priority?.[0],
        due_after: start,
        due_before: end,
        limit: 100, // Maximum allowed by backend API
      });

      // Additional client-side filtering for multiple status/priority values
      const filteredTasks = (response.tasks || []).filter((task) => {
        // Status filter (for multiple values)
        if (filters?.status && filters.status.length > 1 && !filters.status.includes(task.status)) {
          return false;
        }

        // Priority filter (for multiple values)
        if (
          filters?.priority &&
          filters.priority.length > 1 &&
          !filters.priority.includes(task.priority)
        ) {
          return false;
        }

        // Show completed filter
        if (filters?.show_completed === false && task.status === 'done') {
          return false;
        }

        return true;
      });

      return tasksToCalendarEvents(filteredTasks);
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Hook to update task dates when dragging/dropping events
 */
export function useUpdateTaskDates() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      taskId,
      start,
      end,
      allDay,
    }: {
      taskId: string;
      start: Date;
      end: Date;
      allDay: boolean;
    }) => {
      const updateData: Partial<Task> = {};

      if (allDay) {
        // For all-day events, only set due_date
        updateData.due_date = end.toISOString();
        updateData.start_date = undefined;
      } else {
        // For timed events, set both start and due dates
        updateData.start_date = start.toISOString();
        updateData.due_date = end.toISOString();

        // Calculate estimated hours if not set
        const durationHours = (end.getTime() - start.getTime()) / (1000 * 60 * 60);
        if (durationHours > 0 && durationHours <= 24) {
          updateData.estimated_hours = Math.round(durationHours * 2) / 2; // Round to nearest 0.5
        }
      }

      return TasksService.updateTask(taskId, updateData);
    },
    onSuccess: (updatedTask) => {
      // Update the task in all relevant queries
      queryClient.invalidateQueries({ queryKey: ['calendar-tasks'] });
      queryClient.invalidateQueries({ queryKey: ['tasks'] });

      // Optimistically update the task data
      queryClient.setQueryData(['task', updatedTask.id], updatedTask);
    },
    onError: (error) => {
      console.error('Failed to update task dates:', error);
      // Refetch calendar data to revert optimistic updates
      queryClient.invalidateQueries({ queryKey: ['calendar-tasks'] });
    },
  });
}

/**
 * Hook to create new tasks from calendar slots
 */
export function useCreateTaskFromCalendar() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (taskData: Partial<Task>) => {
      return TasksService.createTask(taskData);
    },
    onSuccess: (newTask) => {
      // Invalidate calendar queries to show the new task
      queryClient.invalidateQueries({ queryKey: ['calendar-tasks'] });
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
    onError: (error) => {
      console.error('Failed to create task from calendar:', error);
    },
  });
}

/**
 * Hook to delete tasks from calendar
 */
export function useDeleteTaskFromCalendar() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (taskId: string) => {
      return TasksService.deleteTask(taskId);
    },
    onSuccess: (_, taskId) => {
      // Remove task from calendar
      queryClient.invalidateQueries({ queryKey: ['calendar-tasks'] });
      queryClient.invalidateQueries({ queryKey: ['tasks'] });

      // Remove from individual task cache
      queryClient.removeQueries({ queryKey: ['task', taskId] });
    },
    onError: (error) => {
      console.error('Failed to delete task:', error);
    },
  });
}

/**
 * Hook to update task status quickly from calendar
 */
export function useUpdateTaskStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ taskId, status }: { taskId: string; status: TaskStatus }) => {
      return TasksService.updateTask(taskId, { status });
    },
    onSuccess: (updatedTask) => {
      // Update calendar display
      queryClient.invalidateQueries({ queryKey: ['calendar-tasks'] });

      // Update task data
      queryClient.setQueryData(['task', updatedTask.id], updatedTask);
    },
    onError: (error) => {
      console.error('Failed to update task status:', error);
    },
  });
}

/**
 * Hook for calendar-specific task operations
 */
export function useCalendarOperations() {
  return {
    updateDates: useUpdateTaskDates(),
    createTask: useCreateTaskFromCalendar(),
    deleteTask: useDeleteTaskFromCalendar(),
    updateStatus: useUpdateTaskStatus(),
  };
}

/**
 * Calendar query keys for cache management
 */
export const calendarKeys = {
  all: ['calendar-tasks'] as const,
  range: (startDate: string, endDate: string) => ['calendar-tasks', startDate, endDate] as const,
  filtered: (startDate: string, endDate: string, filters: CalendarFilters) =>
    ['calendar-tasks', startDate, endDate, filters] as const,
};

/**
 * Utility to prefetch calendar data for navigation
 */
export function usePrefetchCalendarData() {
  const queryClient = useQueryClient();

  return {
    prefetchMonth: (date: Date, filters?: CalendarFilters) => {
      const { start, end } = getCalendarDateRange(date, 'month');
      queryClient.prefetchQuery({
        queryKey: calendarKeys.filtered(
          format(start, 'yyyy-MM-dd'),
          format(end, 'yyyy-MM-dd'),
          filters || {}
        ),
        staleTime: 5 * 60 * 1000, // 5 minutes
      });
    },

    prefetchWeek: (date: Date, filters?: CalendarFilters) => {
      const { start, end } = getCalendarDateRange(date, 'week');
      queryClient.prefetchQuery({
        queryKey: calendarKeys.filtered(
          format(start, 'yyyy-MM-dd'),
          format(end, 'yyyy-MM-dd'),
          filters || {}
        ),
        staleTime: 5 * 60 * 1000,
      });
    },
  };
}
