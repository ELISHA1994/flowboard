'use client';

import React, { useState } from 'react';
import { DashboardLayout } from '@/components/layouts/dashboard-layout';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Download, Filter, RefreshCw } from 'lucide-react';

// Dashboard components
import {
  DashboardHeader,
  DashboardSection,
  DashboardGrid,
} from '@/components/dashboard/dashboard-grid';
import { KPIOverview, SecondaryKPICards } from '@/components/dashboard/kpi-cards';

// Chart components
import {
  ProductivityTrendsChart,
  TaskStatusChart,
  TaskPriorityChart,
  CategoryDistributionChart,
  TagDistributionChart,
} from '@/components/charts';

// Analytics hooks
import {
  useAnalyticsDashboard,
  useDerivedMetrics,
  useExportTasksMutation,
} from '@/hooks/use-analytics-query';

export default function AnalyticsPage() {
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [dateRange, setDateRange] = useState<string>('week');

  // Fetch analytics data
  const { statistics, productivity, categories, tags, isLoading, isError, error } =
    useAnalyticsDashboard({
      project_id: selectedProject || undefined,
    });

  // Calculate derived metrics
  const derivedMetrics = useDerivedMetrics(statistics.data, productivity.data);

  // Export functionality
  const exportMutation = useExportTasksMutation();

  const handleExport = (format: 'csv' | 'excel') => {
    exportMutation.mutate({ format });
  };

  const handleRefresh = () => {
    statistics.refetch();
    productivity.refetch();
    categories.refetch();
    tags.refetch();
  };

  return (
    <DashboardLayout>
      <div className="flex-1 space-y-6 p-8 pt-6">
        <DashboardHeader
          title="Analytics"
          description="Track productivity, performance, and task insights"
          actions={
            <div className="flex items-center space-x-2">
              <Select value={dateRange} onValueChange={setDateRange}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Period" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="week">This Week</SelectItem>
                  <SelectItem value="month">This Month</SelectItem>
                  <SelectItem value="quarter">This Quarter</SelectItem>
                </SelectContent>
              </Select>

              <Button variant="outline" size="sm" onClick={handleRefresh}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>

              <Select onValueChange={(value) => handleExport(value as 'csv' | 'excel')}>
                <SelectTrigger className="w-32">
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="csv">Export CSV</SelectItem>
                  <SelectItem value="excel">Export Excel</SelectItem>
                </SelectContent>
              </Select>
            </div>
          }
        />

        {/* Error state */}
        {isError && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="text-sm text-red-600">Failed to load analytics data: {error?.message}</p>
          </div>
        )}

        {/* Main KPI Overview */}
        <DashboardSection title="Key Performance Indicators">
          <KPIOverview
            statistics={statistics.data}
            productivityScore={derivedMetrics?.productivityScore}
            efficiencyTrend={derivedMetrics?.efficiencyTrend}
            totalHoursThisPeriod={derivedMetrics?.totalHoursThisPeriod}
            isLoading={isLoading}
          />
        </DashboardSection>

        {/* Secondary Metrics */}
        <DashboardSection>
          <SecondaryKPICards
            totalTasks={statistics.data?.total_tasks}
            activeProjects={1} // Would come from projects API
            hoursLogged={derivedMetrics?.totalHoursThisPeriod || 0}
            teamMembers={1} // Would come from team API
            isLoading={isLoading}
          />
        </DashboardSection>

        {/* Charts Grid */}
        <DashboardSection title="Analytics Overview">
          <DashboardGrid>
            {/* Productivity Trends - Full width */}
            <div className="col-span-full">
              <ProductivityTrendsChart
                data={productivity.data?.trends || []}
                isLoading={productivity.isLoading}
                error={productivity.error}
              />
            </div>

            {/* Task Status Distribution */}
            <div className="lg:col-span-2">
              <TaskStatusChart
                data={statistics.data?.tasks_by_status || {}}
                isLoading={statistics.isLoading}
                error={statistics.error}
              />
            </div>

            {/* Task Priority Distribution */}
            <div className="lg:col-span-2">
              <TaskPriorityChart
                data={statistics.data?.tasks_by_priority || {}}
                isLoading={statistics.isLoading}
                error={statistics.error}
              />
            </div>

            {/* Category Distribution */}
            <div className="lg:col-span-2">
              <CategoryDistributionChart
                data={categories.data || []}
                isLoading={categories.isLoading}
                error={categories.error}
              />
            </div>

            {/* Tag Distribution */}
            <div className="lg:col-span-2">
              <TagDistributionChart
                data={tags.data || []}
                isLoading={tags.isLoading}
                error={tags.error}
              />
            </div>
          </DashboardGrid>
        </DashboardSection>

        {/* Loading indicator for exports */}
        {exportMutation.isPending && (
          <div className="fixed bottom-4 right-4 bg-primary text-primary-foreground px-4 py-2 rounded-lg shadow-lg">
            <div className="flex items-center space-x-2">
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span>Exporting data...</span>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
