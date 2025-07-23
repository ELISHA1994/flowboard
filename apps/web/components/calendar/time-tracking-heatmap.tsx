'use client';

import React, { useMemo } from 'react';
import {
  format,
  startOfMonth,
  endOfMonth,
  eachDayOfInterval,
  getDay,
  isToday,
  isSameMonth,
} from 'date-fns';
import { cn } from '@/lib/utils';
import { Task } from '@/lib/api/tasks';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Clock, TrendingUp, Calendar } from 'lucide-react';

interface TimeTrackingHeatmapProps {
  tasks: Task[];
  month: Date;
  className?: string;
}

interface DayData {
  date: Date;
  totalHours: number;
  taskCount: number;
  tasks: Task[];
}

export function TimeTrackingHeatmap({ tasks, month, className }: TimeTrackingHeatmapProps) {
  // Process tasks to calculate daily hours
  const dailyData = useMemo(() => {
    const start = startOfMonth(month);
    const end = endOfMonth(month);
    const days = eachDayOfInterval({ start, end });

    const dataMap = new Map<string, DayData>();

    // Initialize all days
    days.forEach((day) => {
      const key = format(day, 'yyyy-MM-dd');
      dataMap.set(key, {
        date: day,
        totalHours: 0,
        taskCount: 0,
        tasks: [],
      });
    });

    // Process tasks and aggregate hours by day
    tasks.forEach((task) => {
      if (task.actual_hours && task.actual_hours > 0) {
        // Use completed_at if available, otherwise use updated_at
        const taskDate = task.completed_at || task.updated_at;
        if (taskDate) {
          const dateKey = format(new Date(taskDate), 'yyyy-MM-dd');
          const dayData = dataMap.get(dateKey);

          if (dayData && isSameMonth(dayData.date, month)) {
            dayData.totalHours += task.actual_hours;
            dayData.taskCount += 1;
            dayData.tasks.push(task);
          }
        }
      }
    });

    return Array.from(dataMap.values());
  }, [tasks, month]);

  // Calculate max hours for intensity scaling
  const maxHours = Math.max(...dailyData.map((d) => d.totalHours), 1);

  // Get the first day of the month's day of week for offset
  const firstDayOfWeek = getDay(startOfMonth(month));

  // Generate intensity color based on hours worked
  const getIntensityColor = (hours: number): string => {
    if (hours === 0) return 'bg-muted';

    const intensity = hours / maxHours;

    if (intensity <= 0.25) return 'bg-green-200 dark:bg-green-900/50';
    if (intensity <= 0.5) return 'bg-green-400 dark:bg-green-700/50';
    if (intensity <= 0.75) return 'bg-green-600 dark:bg-green-500/50';
    return 'bg-green-800 dark:bg-green-400/50';
  };

  // Calculate monthly statistics
  const monthlyStats = useMemo(() => {
    const totalHours = dailyData.reduce((sum, day) => sum + day.totalHours, 0);
    const activeDays = dailyData.filter((day) => day.totalHours > 0).length;
    const avgHoursPerActiveDay = activeDays > 0 ? totalHours / activeDays : 0;
    const totalTasks = dailyData.reduce((sum, day) => sum + day.taskCount, 0);

    return {
      totalHours,
      activeDays,
      avgHoursPerActiveDay,
      totalTasks,
    };
  }, [dailyData]);

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Time Tracking Heatmap
          </CardTitle>
          <div className="text-sm text-muted-foreground">{format(month, 'MMMM yyyy')}</div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Monthly Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-muted-foreground">Total Hours</p>
            <p className="text-lg font-semibold">{monthlyStats.totalHours.toFixed(1)}h</p>
          </div>
          <div>
            <p className="text-muted-foreground">Active Days</p>
            <p className="text-lg font-semibold">{monthlyStats.activeDays}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Avg/Day</p>
            <p className="text-lg font-semibold">{monthlyStats.avgHoursPerActiveDay.toFixed(1)}h</p>
          </div>
          <div>
            <p className="text-muted-foreground">Tasks Done</p>
            <p className="text-lg font-semibold">{monthlyStats.totalTasks}</p>
          </div>
        </div>

        {/* Calendar Heatmap */}
        <div>
          {/* Day labels */}
          <div className="grid grid-cols-7 gap-1 mb-1">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
              <div key={day} className="text-xs text-center text-muted-foreground p-1">
                {day}
              </div>
            ))}
          </div>

          {/* Calendar grid */}
          <div className="grid grid-cols-7 gap-1">
            {/* Empty cells for offset */}
            {Array.from({ length: firstDayOfWeek }).map((_, i) => (
              <div key={`empty-${i}`} />
            ))}

            {/* Day cells */}
            <TooltipProvider>
              {dailyData.map((dayData) => {
                const isCurrentDay = isToday(dayData.date);
                const hasData = dayData.totalHours > 0;

                return (
                  <Tooltip key={format(dayData.date, 'yyyy-MM-dd')}>
                    <TooltipTrigger asChild>
                      <div
                        className={cn(
                          'aspect-square rounded-sm p-1 text-xs flex items-center justify-center cursor-pointer transition-all',
                          getIntensityColor(dayData.totalHours),
                          isCurrentDay && 'ring-2 ring-primary ring-offset-1',
                          hasData && 'hover:scale-110'
                        )}
                      >
                        <span
                          className={cn(
                            'font-medium',
                            dayData.totalHours > 0 && 'text-green-900 dark:text-green-100'
                          )}
                        >
                          {format(dayData.date, 'd')}
                        </span>
                      </div>
                    </TooltipTrigger>

                    <TooltipContent>
                      <div className="space-y-1">
                        <p className="font-semibold">{format(dayData.date, 'MMMM d, yyyy')}</p>
                        {hasData ? (
                          <>
                            <p className="text-sm">
                              <span className="font-medium">{dayData.totalHours.toFixed(1)}h</span>{' '}
                              tracked
                            </p>
                            <p className="text-sm text-muted-foreground">
                              {dayData.taskCount} task{dayData.taskCount !== 1 ? 's' : ''} completed
                            </p>
                            {dayData.tasks.length <= 3 && (
                              <div className="text-xs space-y-0.5 mt-2">
                                {dayData.tasks.map((task, idx) => (
                                  <div key={idx} className="truncate">
                                    • {task.title} ({task.actual_hours}h)
                                  </div>
                                ))}
                              </div>
                            )}
                          </>
                        ) : (
                          <p className="text-sm text-muted-foreground">No time tracked</p>
                        )}
                      </div>
                    </TooltipContent>
                  </Tooltip>
                );
              })}
            </TooltipProvider>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Less</span>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-sm bg-muted" />
            <div className="w-3 h-3 rounded-sm bg-green-200 dark:bg-green-900/50" />
            <div className="w-3 h-3 rounded-sm bg-green-400 dark:bg-green-700/50" />
            <div className="w-3 h-3 rounded-sm bg-green-600 dark:bg-green-500/50" />
            <div className="w-3 h-3 rounded-sm bg-green-800 dark:bg-green-400/50" />
          </div>
          <span className="text-muted-foreground">More</span>
        </div>
      </CardContent>
    </Card>
  );
}

// Weekly time distribution component
export function WeeklyTimeDistribution({
  tasks,
  className,
}: {
  tasks: Task[];
  className?: string;
}) {
  const weeklyData = useMemo(() => {
    const dayTotals = new Array(7).fill(0);
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

    tasks.forEach((task) => {
      if (task.actual_hours && task.actual_hours > 0) {
        const taskDate = task.completed_at || task.updated_at;
        if (taskDate) {
          const dayOfWeek = getDay(new Date(taskDate));
          dayTotals[dayOfWeek] += task.actual_hours;
        }
      }
    });

    const maxHours = Math.max(...dayTotals, 1);

    return dayNames.map((name, index) => ({
      name,
      hours: dayTotals[index],
      percentage: (dayTotals[index] / maxHours) * 100,
    }));
  }, [tasks]);

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          Weekly Pattern
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-3">
        {weeklyData.map((day) => (
          <div key={day.name} className="space-y-1">
            <div className="flex justify-between text-sm">
              <span className="font-medium">{day.name}</span>
              <span className="text-muted-foreground">{day.hours.toFixed(1)}h</span>
            </div>
            <div className="w-full bg-muted rounded-full h-2">
              <div
                className="bg-primary rounded-full h-2 transition-all"
                style={{ width: `${day.percentage}%` }}
              />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

// Export for use in calendar page
export default TimeTrackingHeatmap;
