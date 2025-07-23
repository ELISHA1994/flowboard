'use client';

import React from 'react';
import { CalendarFilters } from '@/hooks/use-calendar-tasks';
import { TaskStatus, TaskPriority } from '@/lib/api/tasks';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Filter,
  X,
  User,
  FolderOpen,
  AlertTriangle,
  CheckCircle2,
  Circle,
  Clock,
} from 'lucide-react';
import { cn } from '@/lib/utils';

// Import projects and users hooks (you may need to implement these)
import { useProjectsQuery } from '@/hooks/use-projects-query';

interface CalendarFiltersPanelProps {
  filters: CalendarFilters;
  onFiltersChange: (filters: CalendarFilters) => void;
  className?: string;
  compact?: boolean;
}

const statusOptions = [
  { value: 'todo', label: 'To Do', icon: Circle, color: 'text-gray-500' },
  { value: 'in_progress', label: 'In Progress', icon: Clock, color: 'text-amber-500' },
  { value: 'done', label: 'Done', icon: CheckCircle2, color: 'text-green-500' },
  { value: 'cancelled', label: 'Cancelled', icon: X, color: 'text-violet-500' },
] as const;

const priorityOptions = [
  { value: 'urgent', label: 'Urgent', color: 'text-red-500' },
  { value: 'high', label: 'High', color: 'text-orange-500' },
  { value: 'medium', label: 'Medium', color: 'text-blue-500' },
  { value: 'low', label: 'Low', color: 'text-green-500' },
] as const;

export function CalendarFiltersPanel({
  filters,
  onFiltersChange,
  className,
  compact = false,
}: CalendarFiltersPanelProps) {
  // Fetch projects for filtering
  const { data: projectsData } = useProjectsQuery();
  const projects = projectsData?.projects || [];

  const updateFilters = (update: Partial<CalendarFilters>) => {
    onFiltersChange({ ...filters, ...update });
  };

  const toggleStatus = (status: TaskStatus) => {
    const currentStatus = filters.status || [];
    const newStatus = currentStatus.includes(status)
      ? currentStatus.filter((s) => s !== status)
      : [...currentStatus, status];

    updateFilters({ status: newStatus });
  };

  const togglePriority = (priority: TaskPriority) => {
    const currentPriorities = filters.priority || [];
    const newPriorities = currentPriorities.includes(priority)
      ? currentPriorities.filter((p) => p !== priority)
      : [...currentPriorities, priority];

    updateFilters({ priority: newPriorities });
  };

  const clearFilters = () => {
    onFiltersChange({
      show_completed: true,
    });
  };

  const hasActiveFilters = Boolean(
    filters.project_id ||
      filters.assigned_to_id ||
      (filters.status && filters.status.length > 0) ||
      (filters.priority && filters.priority.length > 0) ||
      filters.show_completed === false
  );

  if (compact) {
    return (
      <div className={cn('flex items-center gap-2 flex-wrap', className)}>
        {/* Quick Status Filters */}
        <div className="flex items-center gap-1">
          {statusOptions.map(({ value, label, icon: Icon, color }) => {
            const isSelected = filters.status?.includes(value as TaskStatus) ?? false;
            return (
              <Button
                key={value}
                variant={isSelected ? 'default' : 'outline'}
                size="sm"
                onClick={() => toggleStatus(value as TaskStatus)}
                className="h-7 px-2 text-xs"
              >
                <Icon className={cn('h-3 w-3 mr-1', isSelected ? 'text-white' : color)} />
                {label}
              </Button>
            );
          })}
        </div>

        {/* Show/Hide Completed */}
        <Button
          variant={filters.show_completed === false ? 'default' : 'outline'}
          size="sm"
          onClick={() => updateFilters({ show_completed: !filters.show_completed })}
          className="h-7 px-2 text-xs"
        >
          Hide Completed
        </Button>

        {/* Clear Filters */}
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={clearFilters} className="h-7 px-2 text-xs">
            <X className="h-3 w-3 mr-1" />
            Clear
          </Button>
        )}
      </div>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Filter className="h-4 w-4" />
            Calendar Filters
          </CardTitle>
          {hasActiveFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters} className="text-xs">
              <X className="h-3 w-3 mr-1" />
              Clear All
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Project Filter */}
        <div className="space-y-2">
          <label className="text-sm font-medium flex items-center gap-2">
            <FolderOpen className="h-4 w-4" />
            Project
          </label>
          <Select
            value={filters.project_id || 'all'}
            onValueChange={(value) =>
              updateFilters({
                project_id: value === 'all' ? undefined : value,
              })
            }
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="All projects" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All projects</SelectItem>
              {projects.map((project) => (
                <SelectItem key={project.id} value={project.id}>
                  {project.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Status Filters */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Status</label>
          <div className="grid grid-cols-2 gap-2">
            {statusOptions.map(({ value, label, icon: Icon, color }) => {
              const isChecked = filters.status?.includes(value as TaskStatus) ?? false;
              return (
                <div key={value} className="flex items-center space-x-2">
                  <Checkbox
                    id={`status-${value}`}
                    checked={isChecked}
                    onCheckedChange={() => toggleStatus(value as TaskStatus)}
                  />
                  <label
                    htmlFor={`status-${value}`}
                    className="text-sm font-medium cursor-pointer flex items-center gap-2"
                  >
                    <Icon className={cn('h-3 w-3', color)} />
                    {label}
                  </label>
                </div>
              );
            })}
          </div>
        </div>

        {/* Priority Filters */}
        <div className="space-y-2">
          <label className="text-sm font-medium flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            Priority
          </label>
          <div className="grid grid-cols-2 gap-2">
            {priorityOptions.map(({ value, label, color }) => {
              const isChecked = filters.priority?.includes(value as TaskPriority) ?? false;
              return (
                <div key={value} className="flex items-center space-x-2">
                  <Checkbox
                    id={`priority-${value}`}
                    checked={isChecked}
                    onCheckedChange={() => togglePriority(value as TaskPriority)}
                  />
                  <label
                    htmlFor={`priority-${value}`}
                    className="text-sm font-medium cursor-pointer flex items-center gap-2"
                  >
                    <div className={cn('h-2 w-2 rounded-full', color.replace('text-', 'bg-'))} />
                    {label}
                  </label>
                </div>
              );
            })}
          </div>
        </div>

        {/* Show Completed Toggle */}
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="show-completed"
              checked={filters.show_completed !== false}
              onCheckedChange={(checked) =>
                updateFilters({
                  show_completed: checked === false ? false : true,
                })
              }
            />
            <label htmlFor="show-completed" className="text-sm font-medium cursor-pointer">
              Show completed tasks
            </label>
          </div>
        </div>

        {/* Active Filters Summary */}
        {hasActiveFilters && (
          <div className="pt-2 border-t">
            <div className="text-xs text-muted-foreground mb-2">Active filters:</div>
            <div className="flex flex-wrap gap-1">
              {filters.project_id && (
                <Badge variant="secondary" className="text-xs">
                  Project: {projects.find((p) => p.id === filters.project_id)?.name}
                </Badge>
              )}
              {filters.status?.map((status) => (
                <Badge key={status} variant="secondary" className="text-xs">
                  {status.replace('_', ' ')}
                </Badge>
              ))}
              {filters.priority?.map((priority) => (
                <Badge key={priority} variant="secondary" className="text-xs">
                  {priority} priority
                </Badge>
              ))}
              {filters.show_completed === false && (
                <Badge variant="secondary" className="text-xs">
                  Hide completed
                </Badge>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default CalendarFiltersPanel;
