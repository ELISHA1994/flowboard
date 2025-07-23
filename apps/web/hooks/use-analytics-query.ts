import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  AnalyticsService,
  TaskStatistics,
  ProductivityTrendsResponse,
  TimeTrackingReport,
  CategoryDistribution,
  TagDistribution,
  TeamPerformanceReport,
  TimeLogCreate,
  TimeTrackingReportRequest,
  ExportRequest,
  AnalyticsFilters,
} from '@/lib/api/analytics';

// Query Keys
export const analyticsKeys = {
  all: ['analytics'] as const,
  statistics: (filters?: AnalyticsFilters) => ['analytics', 'statistics', filters] as const,
  productivity: (period: string, lookback: number) =>
    ['analytics', 'productivity', period, lookback] as const,
  timeTracking: (request: TimeTrackingReportRequest) =>
    ['analytics', 'time-tracking', request] as const,
  categories: (projectId?: string) => ['analytics', 'categories', projectId] as const,
  tags: (projectId?: string) => ['analytics', 'tags', projectId] as const,
  teamPerformance: (projectId: string) => ['analytics', 'team-performance', projectId] as const,
};

// Hooks for querying analytics data
export function useTaskStatistics(filters?: AnalyticsFilters) {
  return useQuery({
    queryKey: analyticsKeys.statistics(filters),
    queryFn: () => AnalyticsService.getTaskStatistics(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useProductivityTrends(
  period: 'week' | 'month' | 'quarter' = 'week',
  lookback: number = 4
) {
  return useQuery({
    queryKey: analyticsKeys.productivity(period, lookback),
    queryFn: () => AnalyticsService.getProductivityTrends(period, lookback),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

export function useTimeTrackingReport(request: TimeTrackingReportRequest) {
  return useQuery({
    queryKey: analyticsKeys.timeTracking(request),
    queryFn: () => AnalyticsService.getTimeTrackingReport(request),
    enabled: !!request.group_by, // Only run when group_by is specified
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useCategoryDistribution(projectId?: string) {
  return useQuery({
    queryKey: analyticsKeys.categories(projectId),
    queryFn: () => AnalyticsService.getCategoryDistribution(projectId),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

export function useTagDistribution(projectId?: string) {
  return useQuery({
    queryKey: analyticsKeys.tags(projectId),
    queryFn: () => AnalyticsService.getTagDistribution(projectId),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

export function useTeamPerformance(projectId: string) {
  return useQuery({
    queryKey: analyticsKeys.teamPerformance(projectId),
    queryFn: () => AnalyticsService.getTeamPerformance(projectId),
    enabled: !!projectId,
    staleTime: 15 * 60 * 1000, // 15 minutes
  });
}

// Mutations for actions
export function useLogTimeMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ taskId, timeLog }: { taskId: string; timeLog: TimeLogCreate }) =>
      AnalyticsService.logTimeToTask(taskId, timeLog),
    onSuccess: () => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: analyticsKeys.all });
    },
  });
}

export function useExportTasksMutation() {
  return useMutation({
    mutationFn: (request: ExportRequest) => AnalyticsService.exportTasks(request),
    onSuccess: (blob, variables) => {
      const timestamp = new Date().toISOString().slice(0, 16).replace(/[-:]/g, '');
      const extension = variables.format === 'csv' ? 'csv' : 'xlsx';
      const filename = `tasks_${timestamp}.${extension}`;
      AnalyticsService.downloadExportedFile(blob, filename);
    },
  });
}

// Combined hook for dashboard overview
export function useAnalyticsDashboard(filters?: AnalyticsFilters) {
  const statistics = useTaskStatistics(filters);
  const productivity = useProductivityTrends('week', 4);
  const categories = useCategoryDistribution(filters?.project_id);
  const tags = useTagDistribution(filters?.project_id);

  return {
    statistics,
    productivity,
    categories,
    tags,
    isLoading:
      statistics.isLoading || productivity.isLoading || categories.isLoading || tags.isLoading,
    isError: statistics.isError || productivity.isError || categories.isError || tags.isError,
    error: statistics.error || productivity.error || categories.error || tags.error,
  };
}

// Hook for derived metrics
export function useDerivedMetrics(
  statistics?: TaskStatistics,
  productivity?: ProductivityTrendsResponse
) {
  if (!statistics || !productivity) {
    return null;
  }

  return {
    productivityScore: AnalyticsService.calculateProductivityScore(statistics),
    efficiencyTrend: AnalyticsService.calculateEfficiencyTrend(productivity.trends),
    totalTasksThisPeriod: productivity.trends[productivity.trends.length - 1]?.tasks_created || 0,
    totalCompletedThisPeriod:
      productivity.trends[productivity.trends.length - 1]?.tasks_completed || 0,
    totalHoursThisPeriod: productivity.trends[productivity.trends.length - 1]?.hours_logged || 0,
  };
}
