import { useState, useEffect } from 'react';
import { TasksService, Task, TaskStatistics } from '@/lib/api/tasks';

export function useTasks(params?: Parameters<typeof TasksService.getTasks>[0]) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await TasksService.getTasks(params);
      setTasks(response.tasks);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch tasks');
      setTasks([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, [JSON.stringify(params)]); // Serialize params for dependency

  return { tasks, loading, error, total, refetch: fetchTasks };
}

export function useTaskStatistics(params?: Parameters<typeof TasksService.getStatistics>[0]) {
  const [statistics, setStatistics] = useState<TaskStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStatistics = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await TasksService.getStatistics(params);
        setStatistics(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch statistics');
        setStatistics(null);
      } finally {
        setLoading(false);
      }
    };

    fetchStatistics();
  }, [JSON.stringify(params)]);

  return { statistics, loading, error };
}

export function useRecentTasks(limit: number = 5) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRecentTasks = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await TasksService.getRecentTasks(limit);
        setTasks(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch recent tasks');
        setTasks([]);
      } finally {
        setLoading(false);
      }
    };

    fetchRecentTasks();
  }, [limit]);

  return { tasks, loading, error };
}

export function useUpcomingTasks(days: number = 7) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUpcomingTasks = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await TasksService.getUpcomingTasks(days);
        setTasks(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch upcoming tasks');
        setTasks([]);
      } finally {
        setLoading(false);
      }
    };

    fetchUpcomingTasks();
  }, [days]);

  return { tasks, loading, error };
}
