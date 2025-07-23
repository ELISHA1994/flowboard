'use client';

import React, { useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import {
  BarChart3,
  Clock,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Task } from '@/types/api';

interface TeamMemberPerformance {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  totalTasks: number;
  completedTasks: number;
  inProgressTasks: number;
  overdueTasks: number;
  totalHours: number;
  averageCompletionTime: number; // in days
  completionRate: number; // percentage
  productivityScore: number; // 0-100
  trend: 'up' | 'down' | 'stable';
}

interface TeamPerformanceChartProps {
  tasks: Task[];
  teamMembers: Array<{
    id: string;
    name: string;
    email: string;
    avatar?: string;
  }>;
  className?: string;
  showDetails?: boolean;
}

export function TeamPerformanceChart({
  tasks,
  teamMembers,
  className,
  showDetails = true,
}: TeamPerformanceChartProps) {
  // Calculate performance metrics for each team member
  const performanceData = useMemo(() => {
    const memberPerformance = new Map<string, TeamMemberPerformance>();

    // Initialize performance data for each team member
    teamMembers.forEach((member) => {
      memberPerformance.set(member.id, {
        ...member,
        totalTasks: 0,
        completedTasks: 0,
        inProgressTasks: 0,
        overdueTasks: 0,
        totalHours: 0,
        averageCompletionTime: 0,
        completionRate: 0,
        productivityScore: 0,
        trend: 'stable',
      });
    });

    // Process tasks to calculate metrics
    tasks.forEach((task) => {
      if (task.assigned_to_id && memberPerformance.has(task.assigned_to_id)) {
        const member = memberPerformance.get(task.assigned_to_id)!;

        member.totalTasks++;

        // Count by status
        if (task.status === 'done') {
          member.completedTasks++;

          // Calculate completion time if dates available
          if (task.created_at && task.updated_at) {
            const createdDate = new Date(task.created_at);
            const completedDate = new Date(task.updated_at);
            const completionDays = Math.ceil(
              (completedDate.getTime() - createdDate.getTime()) / (1000 * 60 * 60 * 24)
            );
            member.averageCompletionTime =
              (member.averageCompletionTime * (member.completedTasks - 1) + completionDays) /
              member.completedTasks;
          }
        } else if (task.status === 'in_progress') {
          member.inProgressTasks++;
        }

        // Check if overdue
        if (task.due_date && new Date(task.due_date) < new Date() && task.status !== 'done') {
          member.overdueTasks++;
        }

        // Add actual hours
        if (task.actual_hours) {
          member.totalHours += task.actual_hours;
        }
      }
    });

    // Calculate final metrics and scores
    memberPerformance.forEach((member, id) => {
      // Completion rate
      member.completionRate =
        member.totalTasks > 0 ? Math.round((member.completedTasks / member.totalTasks) * 100) : 0;

      // Productivity score (weighted calculation)
      const completionWeight = 0.4;
      const overdueWeight = 0.3;
      const efficiencyWeight = 0.3;

      const completionScore = member.completionRate;
      const overdueScore =
        member.totalTasks > 0
          ? Math.max(0, 100 - (member.overdueTasks / member.totalTasks) * 100)
          : 100;
      const efficiencyScore =
        member.averageCompletionTime > 0
          ? Math.max(0, 100 - Math.min(member.averageCompletionTime * 5, 100))
          : 50;

      member.productivityScore = Math.round(
        completionScore * completionWeight +
          overdueScore * overdueWeight +
          efficiencyScore * efficiencyWeight
      );

      // Determine trend (in real app, this would compare to previous period)
      if (member.productivityScore >= 80) member.trend = 'up';
      else if (member.productivityScore <= 50) member.trend = 'down';
    });

    return Array.from(memberPerformance.values()).sort(
      (a, b) => b.productivityScore - a.productivityScore
    );
  }, [tasks, teamMembers]);

  // Find max values for scaling
  const maxTasks = Math.max(...performanceData.map((m) => m.totalTasks), 1);
  const maxHours = Math.max(...performanceData.map((m) => m.totalHours), 1);

  return (
    <Card className={cn('w-full', className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Team Performance</CardTitle>
            <CardDescription>Comparative analysis of team member productivity</CardDescription>
          </div>
          <BarChart3 className="h-5 w-5 text-muted-foreground" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {performanceData.map((member, index) => (
            <div key={member.id} className="space-y-3">
              {/* Member Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Avatar className="h-10 w-10">
                    <AvatarImage src={member.avatar} alt={member.name} />
                    <AvatarFallback>
                      {member.name
                        .split(' ')
                        .map((n) => n[0])
                        .join('')
                        .toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-medium">{member.name}</p>
                      {index === 0 && (
                        <Badge variant="default" className="text-xs">
                          Top Performer
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">{member.email}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-right">
                    <p className="text-2xl font-bold">{member.productivityScore}</p>
                    <p className="text-xs text-muted-foreground">Score</p>
                  </div>
                  {member.trend === 'up' && <TrendingUp className="h-4 w-4 text-green-500" />}
                  {member.trend === 'down' && <TrendingDown className="h-4 w-4 text-red-500" />}
                </div>
              </div>

              {/* Performance Bars */}
              <div className="space-y-2">
                {/* Tasks Progress Bar */}
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-muted-foreground">Tasks</span>
                    <span className="font-medium">{member.totalTasks}</span>
                  </div>
                  <Progress value={(member.totalTasks / maxTasks) * 100} className="h-2" />
                </div>

                {/* Hours Progress Bar */}
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-muted-foreground">Hours Tracked</span>
                    <span className="font-medium">{member.totalHours.toFixed(1)}h</span>
                  </div>
                  <Progress value={(member.totalHours / maxHours) * 100} className="h-2" />
                </div>

                {/* Completion Rate */}
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-muted-foreground">Completion Rate</span>
                    <span className="font-medium">{member.completionRate}%</span>
                  </div>
                  <Progress value={member.completionRate} className="h-2" />
                </div>
              </div>

              {/* Detailed Stats */}
              {showDetails && (
                <div className="grid grid-cols-4 gap-2 pt-2">
                  <div className="text-center">
                    <CheckCircle2 className="h-4 w-4 mx-auto mb-1 text-green-500" />
                    <p className="text-xs font-medium">{member.completedTasks}</p>
                    <p className="text-xs text-muted-foreground">Done</p>
                  </div>
                  <div className="text-center">
                    <Clock className="h-4 w-4 mx-auto mb-1 text-blue-500" />
                    <p className="text-xs font-medium">{member.inProgressTasks}</p>
                    <p className="text-xs text-muted-foreground">Active</p>
                  </div>
                  <div className="text-center">
                    <AlertCircle className="h-4 w-4 mx-auto mb-1 text-orange-500" />
                    <p className="text-xs font-medium">{member.overdueTasks}</p>
                    <p className="text-xs text-muted-foreground">Overdue</p>
                  </div>
                  <div className="text-center">
                    <BarChart3 className="h-4 w-4 mx-auto mb-1 text-purple-500" />
                    <p className="text-xs font-medium">
                      {member.averageCompletionTime > 0
                        ? `${member.averageCompletionTime.toFixed(1)}d`
                        : 'N/A'}
                    </p>
                    <p className="text-xs text-muted-foreground">Avg Time</p>
                  </div>
                </div>
              )}
            </div>
          ))}

          {/* Empty State */}
          {performanceData.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <BarChart3 className="h-12 w-12 mx-auto mb-3 opacity-20" />
              <p>No team performance data available</p>
              <p className="text-sm mt-1">Assign tasks to team members to see their performance</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Simplified version for dashboard widgets
export function TeamPerformanceSummary({
  tasks,
  teamMembers,
  className,
}: Omit<TeamPerformanceChartProps, 'showDetails'>) {
  return (
    <TeamPerformanceChart
      tasks={tasks}
      teamMembers={teamMembers}
      className={className}
      showDetails={false}
    />
  );
}
