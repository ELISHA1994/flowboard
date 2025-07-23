'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  CheckCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  Target,
  Timer,
  Users,
  BarChart3,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { TaskStatistics } from '@/lib/api/analytics';
import { AnalyticsService } from '@/lib/api/analytics';

interface KPICardProps {
  title: string;
  value: string | number;
  description?: string;
  icon: React.ElementType;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: string;
  className?: string;
  isLoading?: boolean;
}

export function KPICard({
  title,
  value,
  description,
  icon: Icon,
  trend,
  trendValue,
  className,
  isLoading = false,
}: KPICardProps) {
  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-600" />;
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-600" />;
      default:
        return <Minus className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return 'text-green-600';
      case 'down':
        return 'text-red-600';
      default:
        return 'text-muted-foreground';
    }
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
          <Icon className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="h-8 w-20 bg-muted animate-pulse rounded" />
            <div className="h-4 w-32 bg-muted animate-pulse rounded" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {(description || trendValue) && (
          <div className="flex items-center space-x-2 text-xs text-muted-foreground mt-1">
            {trendValue && (
              <div className="flex items-center space-x-1">
                {getTrendIcon()}
                <span className={getTrendColor()}>{trendValue}</span>
              </div>
            )}
            {description && <span className="flex-1">{description}</span>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface KPIOverviewProps {
  statistics?: TaskStatistics;
  productivityScore?: number;
  efficiencyTrend?: 'up' | 'down' | 'stable';
  totalHoursThisPeriod?: number;
  isLoading?: boolean;
}

export function KPIOverview({
  statistics,
  productivityScore,
  efficiencyTrend,
  totalHoursThisPeriod,
  isLoading = false,
}: KPIOverviewProps) {
  const completionRate = statistics ? Math.round(statistics.completion_rate * 100) : 0;
  const avgCompletionTime = statistics?.average_completion_time || 0;
  const overdueCount = statistics?.overdue_tasks || 0;

  const formatHours = (hours: number) => {
    return AnalyticsService.formatHours(hours);
  };

  const formatAvgTime = (days: number) => {
    if (days < 1) {
      return `${Math.round(days * 24)}h`;
    }
    return `${Math.round(days)}d`;
  };

  return (
    <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
      <KPICard
        title="Task Completion Rate"
        value={`${completionRate}%`}
        description="Tasks completed vs total"
        icon={CheckCircle}
        trend={completionRate >= 80 ? 'up' : completionRate >= 60 ? 'stable' : 'down'}
        isLoading={isLoading}
      />

      <KPICard
        title="Productivity Score"
        value={productivityScore || 0}
        description="Based on completion metrics"
        icon={Target}
        trend={efficiencyTrend}
        trendValue={efficiencyTrend !== 'stable' ? 'vs last period' : undefined}
        isLoading={isLoading}
      />

      <KPICard
        title="Average Completion Time"
        value={formatAvgTime(avgCompletionTime)}
        description="Time to complete tasks"
        icon={Clock}
        trend={avgCompletionTime <= 2 ? 'up' : avgCompletionTime <= 5 ? 'stable' : 'down'}
        isLoading={isLoading}
      />

      <KPICard
        title="Overdue Tasks"
        value={overdueCount}
        description="Tasks past due date"
        icon={AlertTriangle}
        trend={overdueCount === 0 ? 'up' : overdueCount <= 3 ? 'stable' : 'down'}
        className={overdueCount > 5 ? 'border-red-200 bg-red-50/50' : undefined}
        isLoading={isLoading}
      />
    </div>
  );
}

interface SecondaryKPIProps {
  totalTasks?: number;
  activeProjects?: number;
  hoursLogged?: number;
  teamMembers?: number;
  isLoading?: boolean;
}

export function SecondaryKPICards({
  totalTasks = 0,
  activeProjects = 0,
  hoursLogged = 0,
  teamMembers = 0,
  isLoading = false,
}: SecondaryKPIProps) {
  return (
    <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
      <KPICard
        title="Total Tasks"
        value={totalTasks.toLocaleString()}
        description="All tasks"
        icon={BarChart3}
        isLoading={isLoading}
      />

      <KPICard
        title="Active Projects"
        value={activeProjects}
        description="In progress"
        icon={Target}
        isLoading={isLoading}
      />

      <KPICard
        title="Hours Logged"
        value={AnalyticsService.formatHours(hoursLogged)}
        description="This period"
        icon={Timer}
        isLoading={isLoading}
      />

      <KPICard
        title="Team Members"
        value={teamMembers}
        description="Active users"
        icon={Users}
        isLoading={isLoading}
      />
    </div>
  );
}

// Specialized KPI cards for specific metrics
export function CompletionRateCard({
  completionRate,
  previousRate,
  isLoading = false,
}: {
  completionRate: number;
  previousRate?: number;
  isLoading?: boolean;
}) {
  const rate = Math.round(completionRate * 100);
  const prevRate = previousRate ? Math.round(previousRate * 100) : undefined;
  const diff = prevRate ? rate - prevRate : undefined;

  const trend: 'up' | 'down' | 'stable' =
    diff === undefined ? 'stable' : diff > 2 ? 'up' : diff < -2 ? 'down' : 'stable';

  return (
    <KPICard
      title="Completion Rate"
      value={`${rate}%`}
      description="Tasks completed successfully"
      icon={CheckCircle}
      trend={trend}
      trendValue={diff ? `${diff > 0 ? '+' : ''}${diff}% from last period` : undefined}
      isLoading={isLoading}
    />
  );
}

export function EfficiencyCard({
  averageTime,
  previousTime,
  isLoading = false,
}: {
  averageTime: number;
  previousTime?: number;
  isLoading?: boolean;
}) {
  const formatTime = (days: number) => {
    if (days < 1) return `${Math.round(days * 24)}h`;
    return `${Math.round(days * 10) / 10}d`;
  };

  const trend: 'up' | 'down' | 'stable' = !previousTime
    ? 'stable'
    : averageTime < previousTime * 0.9
      ? 'up'
      : averageTime > previousTime * 1.1
        ? 'down'
        : 'stable';

  return (
    <KPICard
      title="Avg Completion Time"
      value={formatTime(averageTime)}
      description="Time to complete tasks"
      icon={Clock}
      trend={trend}
      trendValue={
        previousTime
          ? `${trend === 'up' ? 'Faster' : trend === 'down' ? 'Slower' : 'Similar'} than last period`
          : undefined
      }
      isLoading={isLoading}
    />
  );
}
