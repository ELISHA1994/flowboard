'use client';

import React, { useState, useMemo } from 'react';
import {
  format,
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  eachDayOfInterval,
  isSameMonth,
  isSameDay,
  isToday,
  addMonths,
  subMonths,
} from 'date-fns';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon, Clock, Flag } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Task, TaskPriority } from '@/lib/api/tasks';
import { useRouter } from 'next/navigation';

interface TaskCalendarProps {
  tasks: Task[];
  onTaskClick?: (task: Task) => void;
  className?: string;
}

export function TaskCalendar({ tasks, onTaskClick, className }: TaskCalendarProps) {
  const router = useRouter();
  const [currentDate, setCurrentDate] = useState(new Date());

  const monthStart = startOfMonth(currentDate);
  const monthEnd = endOfMonth(currentDate);
  const calendarStart = startOfWeek(monthStart);
  const calendarEnd = endOfWeek(monthEnd);

  const calendarDays = eachDayOfInterval({
    start: calendarStart,
    end: calendarEnd,
  });

  // Group tasks by date
  const tasksByDate = useMemo(() => {
    const grouped: Record<string, Task[]> = {};

    tasks.forEach((task) => {
      if (task.due_date) {
        const dateKey = format(new Date(task.due_date), 'yyyy-MM-dd');
        if (!grouped[dateKey]) {
          grouped[dateKey] = [];
        }
        grouped[dateKey].push(task);
      }
    });

    return grouped;
  }, [tasks]);

  const getPriorityColor = (priority: TaskPriority) => {
    switch (priority) {
      case 'urgent':
        return 'bg-red-500';
      case 'high':
        return 'bg-orange-500';
      case 'medium':
        return 'bg-yellow-500';
      case 'low':
        return 'bg-green-500';
      default:
        return 'bg-gray-500';
    }
  };

  const handleTaskClick = (task: Task) => {
    if (onTaskClick) {
      onTaskClick(task);
    } else {
      router.push(`/tasks/${task.id}`);
    }
  };

  const navigateMonth = (direction: 'prev' | 'next') => {
    setCurrentDate((prev) => (direction === 'prev' ? subMonths(prev, 1) : addMonths(prev, 1)));
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  return (
    <div className={cn('w-full', className)}>
      {/* Calendar Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-semibold">{format(currentDate, 'MMMM yyyy')}</h2>
          <Button variant="outline" size="sm" onClick={goToToday} className="text-sm">
            <CalendarIcon className="mr-2 h-4 w-4" />
            Today
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => navigateMonth('prev')}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={() => navigateMonth('next')}>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="grid grid-cols-7 gap-px bg-border rounded-lg overflow-hidden">
        {/* Day Headers */}
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
          <div
            key={day}
            className="bg-muted px-2 py-3 text-center text-sm font-medium text-muted-foreground"
          >
            {day}
          </div>
        ))}

        {/* Calendar Days */}
        {calendarDays.map((day) => {
          const dateKey = format(day, 'yyyy-MM-dd');
          const dayTasks = tasksByDate[dateKey] || [];
          const isCurrentMonth = isSameMonth(day, currentDate);
          const isToday_ = isToday(day);

          return (
            <div
              key={day.toISOString()}
              className={cn(
                'bg-card min-h-[120px] p-2 transition-colors hover:bg-muted/50',
                !isCurrentMonth && 'opacity-50'
              )}
            >
              {/* Date Number */}
              <div className="flex items-center justify-between mb-1">
                <span
                  className={cn(
                    'text-sm font-medium',
                    isToday_ &&
                      'bg-primary text-primary-foreground rounded-full w-6 h-6 flex items-center justify-center text-xs'
                  )}
                >
                  {format(day, 'd')}
                </span>

                {dayTasks.length > 0 && (
                  <Badge variant="outline" className="text-xs h-5 px-1">
                    {dayTasks.length}
                  </Badge>
                )}
              </div>

              {/* Tasks for this day */}
              <div className="space-y-1">
                {dayTasks.slice(0, 3).map((task) => (
                  <div
                    key={task.id}
                    onClick={() => handleTaskClick(task)}
                    className={cn(
                      'group cursor-pointer rounded px-2 py-1 text-xs',
                      'hover:bg-accent hover:text-accent-foreground',
                      'border-l-2 bg-muted/50',
                      getPriorityColor(task.priority)
                    )}
                    style={{
                      borderLeftColor: `var(--${getPriorityColor(task.priority).replace('bg-', '')})`,
                    }}
                  >
                    <div className="flex items-center gap-1">
                      {task.status === 'done' ? (
                        <div className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0" />
                      ) : task.status === 'in_progress' ? (
                        <Clock className="w-2 h-2 text-blue-500 flex-shrink-0" />
                      ) : (
                        <div className="w-2 h-2 rounded-full border border-muted-foreground flex-shrink-0" />
                      )}
                      <span
                        className={cn(
                          'truncate flex-1',
                          task.status === 'done' && 'line-through text-muted-foreground'
                        )}
                      >
                        {task.title}
                      </span>
                    </div>
                  </div>
                ))}

                {dayTasks.length > 3 && (
                  <div className="text-xs text-muted-foreground px-2 py-1">
                    +{dayTasks.length - 3} more
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-4 flex items-center gap-6 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-red-500" />
          <span>Urgent</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-orange-500" />
          <span>High</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-yellow-500" />
          <span>Medium</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-green-500" />
          <span>Low</span>
        </div>
      </div>
    </div>
  );
}
