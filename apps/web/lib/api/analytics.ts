import { ApiClient } from '@/lib/api-client';
import { AuthService } from '@/lib/auth';

// Analytics Data Types
export interface TaskStatistics {
  total_tasks: number;
  tasks_by_status: Record<string, number>;
  tasks_by_priority: Record<string, number>;
  completion_rate: number;
  average_completion_time: number;
  overdue_tasks: number;
  date_range?: {
    start_date: string;
    end_date: string;
  };
}

export interface ProductivityTrend {
  period_start: string;
  period_end: string;
  tasks_created: number;
  tasks_completed: number;
  hours_logged: number;
}

export interface ProductivityTrendsResponse {
  period_type: string;
  trends: ProductivityTrend[];
}

export interface TimeTrackingEntry {
  task_id?: string;
  task_title?: string;
  project_id?: string;
  project_name?: string;
  date?: string;
  total_hours: number;
  log_count: number;
}

export interface TimeTrackingReport {
  total_hours: number;
  group_by: string;
  entries: TimeTrackingEntry[];
  date_range: {
    start_date: string;
    end_date: string;
  };
}

export interface CategoryDistribution {
  category_id: string;
  category_name: string;
  color: string;
  task_count: number;
}

export interface TagDistribution {
  tag_id: string;
  tag_name: string;
  color: string;
  task_count: number;
}

export interface TeamMemberPerformance {
  user_id: string;
  username: string;
  role: string;
  tasks_assigned: number;
  tasks_completed: number;
  hours_logged: number;
}

export interface TeamPerformanceReport {
  project_id: string;
  project_name: string;
  team_members: TeamMemberPerformance[];
}

export interface TimeLogCreate {
  hours: number;
  description?: string;
  logged_at?: string;
}

export interface TimeLogResponse {
  id: string;
  task_id: string;
  user_id: string;
  hours: number;
  description?: string;
  logged_at: string;
  created_at: string;
}

export interface ExportRequest {
  format: 'csv' | 'excel';
  task_ids?: string[];
}

export interface TimeTrackingReportRequest {
  start_date?: string;
  end_date?: string;
  group_by: 'task' | 'project' | 'category' | 'day';
}

export interface AnalyticsFilters {
  start_date?: string;
  end_date?: string;
  project_id?: string;
}

// Analytics API Service
export class AnalyticsService {
  private static async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    return ApiClient.fetchJSON(ApiClient.buildUrl(`/analytics${endpoint}`), options);
  }

  // Task Statistics
  static async getTaskStatistics(filters?: AnalyticsFilters): Promise<TaskStatistics> {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    if (filters?.project_id) params.append('project_id', filters.project_id);

    const query = params.toString() ? `?${params.toString()}` : '';
    return this.makeRequest<TaskStatistics>(`/statistics${query}`);
  }

  // Productivity Trends
  static async getProductivityTrends(
    period: 'week' | 'month' | 'quarter' = 'week',
    lookback: number = 4
  ): Promise<ProductivityTrendsResponse> {
    const params = new URLSearchParams({
      period,
      lookback: lookback.toString(),
    });

    return this.makeRequest<ProductivityTrendsResponse>(
      `/productivity-trends?${params.toString()}`
    );
  }

  // Time Tracking Report
  static async getTimeTrackingReport(
    request: TimeTrackingReportRequest
  ): Promise<TimeTrackingReport> {
    return this.makeRequest<TimeTrackingReport>('/time-tracking/report', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Category Distribution
  static async getCategoryDistribution(project_id?: string): Promise<CategoryDistribution[]> {
    const params = project_id ? `?project_id=${project_id}` : '';
    return this.makeRequest<CategoryDistribution[]>(`/category-distribution${params}`);
  }

  // Tag Distribution
  static async getTagDistribution(project_id?: string): Promise<TagDistribution[]> {
    const params = project_id ? `?project_id=${project_id}` : '';
    return this.makeRequest<TagDistribution[]>(`/tag-distribution${params}`);
  }

  // Team Performance
  static async getTeamPerformance(project_id: string): Promise<TeamPerformanceReport> {
    return this.makeRequest<TeamPerformanceReport>(`/team-performance/${project_id}`);
  }

  // Log Time to Task
  static async logTimeToTask(task_id: string, time_log: TimeLogCreate): Promise<TimeLogResponse> {
    return this.makeRequest<TimeLogResponse>(`/tasks/${task_id}/time-log`, {
      method: 'POST',
      body: JSON.stringify(time_log),
    });
  }

  // Export Data
  static async exportTasks(request: ExportRequest): Promise<Blob> {
    const response = await fetch(ApiClient.buildUrl('/analytics/export'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${AuthService.getToken()}`,
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error('Export failed');
    }

    return response.blob();
  }

  // Helper method to download exported file
  static downloadExportedFile(blob: Blob, filename: string) {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  // Calculate derived metrics for dashboard
  static calculateProductivityScore(stats: TaskStatistics): number {
    if (stats.total_tasks === 0) return 0;
    return Math.round(stats.completion_rate * 100);
  }

  static calculateEfficiencyTrend(trends: ProductivityTrend[]): 'up' | 'down' | 'stable' {
    if (trends.length < 2) return 'stable';

    const latest = trends[trends.length - 1];
    const previous = trends[trends.length - 2];

    const latestEfficiency = latest.tasks_completed / Math.max(latest.tasks_created, 1);
    const previousEfficiency = previous.tasks_completed / Math.max(previous.tasks_created, 1);

    if (latestEfficiency > previousEfficiency * 1.05) return 'up';
    if (latestEfficiency < previousEfficiency * 0.95) return 'down';
    return 'stable';
  }

  static formatHours(hours: number): string {
    const h = Math.floor(hours);
    const m = Math.round((hours - h) * 60);
    return m > 0 ? `${h}h ${m}m` : `${h}h`;
  }
}
