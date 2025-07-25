'use client';

import React from 'react';
import { ToolbarProps, View } from 'react-big-calendar';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight, Calendar, Plus, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';

interface CalendarToolbarProps extends ToolbarProps {
  onNavigate: (direction: 'prev' | 'next' | 'today') => void;
  isLoading?: boolean;
  onCreateTask?: () => void;
}

export function CalendarToolbar({
  date,
  view,
  views,
  label,
  onNavigate,
  onView,
  isLoading = false,
  onCreateTask,
}: CalendarToolbarProps) {
  const viewButtons = [
    { key: 'month' as View, label: 'Month' },
    { key: 'week' as View, label: 'Week' },
    { key: 'work_week' as View, label: 'Work Week' },
    { key: 'day' as View, label: 'Day' },
    { key: 'agenda' as View, label: 'Agenda' },
  ];

  return (
    <div className="calendar-toolbar">
      {/* Navigation Controls */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => onNavigate('prev')}
          disabled={isLoading}
          className="h-9 w-9"
        >
          <ChevronLeft className="h-4 w-4" />
          <span className="sr-only">Previous</span>
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={() => onNavigate('today')}
          disabled={isLoading}
          className="px-4"
        >
          <Calendar className="h-4 w-4 mr-2" />
          Today
        </Button>

        <Button
          variant="ghost"
          size="icon"
          onClick={() => onNavigate('next')}
          disabled={isLoading}
          className="h-9 w-9"
        >
          <ChevronRight className="h-4 w-4" />
          <span className="sr-only">Next</span>
        </Button>
      </div>

      {/* Current Date/Range Label */}
      <div className="flex items-center gap-4">
        {isLoading && <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />}
        <h3 className="text-xl font-bold text-foreground">{label}</h3>
      </div>

      {/* View Switcher and Actions */}
      <div className="flex items-center gap-2">
        {/* View Buttons */}
        <div className="hidden sm:flex items-center gap-1 calendar-toolbar-views">
          {viewButtons.map(({ key, label: viewLabel }) => {
            // Check if view is available
            if (views && !views[key]) return null;

            return (
              <Button
                key={key}
                variant={view === key ? 'default' : 'ghost'}
                size="sm"
                onClick={() => onView(key)}
                disabled={isLoading}
                className={cn('text-xs h-7 px-2', view === key && 'gradient-button shadow-sm')}
              >
                {viewLabel}
              </Button>
            );
          })}
        </div>

        {/* Mobile View Selector */}
        <div className="sm:hidden">
          <select
            value={view}
            onChange={(e) => onView(e.target.value as View)}
            className="px-3 py-1 border rounded text-sm bg-white dark:bg-gray-950"
            disabled={isLoading}
          >
            {viewButtons.map(({ key, label: viewLabel }) => {
              if (views && !views[key]) return null;
              return (
                <option key={key} value={key}>
                  {viewLabel}
                </option>
              );
            })}
          </select>
        </div>

        {/* Create Task Button */}
        {onCreateTask && (
          <Button
            variant="primary"
            size="sm"
            onClick={onCreateTask}
            disabled={isLoading}
            className="ml-4 shadow-md"
          >
            <Plus className="h-4 w-4 mr-2" />
            <span className="hidden sm:inline">New Task</span>
            <span className="sm:hidden">New</span>
          </Button>
        )}
      </div>
    </div>
  );
}

// Additional toolbar utilities
export function getToolbarTitle(date: Date, view: View): string {
  switch (view) {
    case 'month':
      return format(date, 'MMMM yyyy');
    case 'week':
    case 'work_week':
      // Get start and end of week for range display
      const startOfWeekDate = new Date(date);
      startOfWeekDate.setDate(date.getDate() - date.getDay());
      const endOfWeekDate = new Date(startOfWeekDate);
      endOfWeekDate.setDate(startOfWeekDate.getDate() + 6);

      if (startOfWeekDate.getMonth() === endOfWeekDate.getMonth()) {
        return `${format(startOfWeekDate, 'MMM d')} - ${format(endOfWeekDate, 'd, yyyy')}`;
      } else {
        return `${format(startOfWeekDate, 'MMM d')} - ${format(endOfWeekDate, 'MMM d, yyyy')}`;
      }
    case 'day':
      return format(date, 'EEEE, MMMM d, yyyy');
    case 'agenda':
      return `Agenda - ${format(date, 'MMMM yyyy')}`;
    default:
      return format(date, 'MMMM yyyy');
  }
}

// Export types for consistency
export type { CalendarToolbarProps };
