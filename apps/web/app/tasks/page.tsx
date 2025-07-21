'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuCheckboxItem,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Plus,
  Search,
  Filter,
  MoreHorizontal,
  Calendar,
  Clock,
  Flag,
  CheckCircle2,
  Circle,
  XCircle,
  Edit,
  Trash2,
  Copy,
  Share2,
  Archive,
  ChevronDown,
  Grid3X3,
  List,
  Kanban,
  CalendarDays,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { TasksService, Task, TaskStatus, TaskPriority } from '@/lib/api/tasks';
import { CreateTaskModal } from '@/components/tasks/create-task-modal';
import { TaskCalendar } from '@/components/tasks/task-calendar';
import { DashboardLayout } from '@/components/layouts/dashboard-layout';
import { format } from 'date-fns';
import { useToast } from '@/hooks/use-toast';

type ViewMode = 'list' | 'board' | 'calendar';

export default function TasksPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [selectedTasks, setSelectedTasks] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<TaskStatus | 'all'>('all');
  const [priorityFilter, setPriorityFilter] = useState<TaskPriority | 'all'>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [sortBy, setSortBy] = useState<string>('position');

  // Fetch tasks
  const fetchTasks = useCallback(async () => {
    try {
      setLoading(true);
      const response = await TasksService.getTasks({
        status: statusFilter === 'all' ? undefined : statusFilter,
        priority: priorityFilter === 'all' ? undefined : priorityFilter,
        sort_by: sortBy,
        limit: 100,
      });
      setTasks(response.tasks || []);
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
      toast({
        title: 'Error',
        description: 'Failed to load tasks. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [statusFilter, priorityFilter, sortBy, toast]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  // Filter tasks based on search
  const filteredTasks = tasks.filter(
    (task) =>
      task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      task.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Handle task selection
  const handleSelectTask = (taskId: string) => {
    setSelectedTasks((prev) =>
      prev.includes(taskId) ? prev.filter((id) => id !== taskId) : [...prev, taskId]
    );
  };

  const handleSelectAll = () => {
    if (selectedTasks.length === filteredTasks.length) {
      setSelectedTasks([]);
    } else {
      setSelectedTasks(filteredTasks.map((task) => task.id));
    }
  };

  // Handle bulk actions
  const handleBulkDelete = async () => {
    if (selectedTasks.length === 0) return;

    try {
      await Promise.all(selectedTasks.map((taskId) => TasksService.deleteTask(taskId)));
      toast({
        title: 'Success',
        description: `${selectedTasks.length} tasks deleted successfully`,
      });
      setSelectedTasks([]);
      fetchTasks();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete tasks. Please try again.',
        variant: 'destructive',
      });
    }
  };

  // Get status icon
  const getStatusIcon = (status: TaskStatus) => {
    switch (status) {
      case 'done':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'in_progress':
        return <Clock className="h-4 w-4 text-blue-600" />;
      case 'cancelled':
        return <XCircle className="h-4 w-4 text-gray-400" />;
      default:
        return <Circle className="h-4 w-4 text-gray-400" />;
    }
  };

  // Get priority badge
  const getPriorityBadge = (priority: TaskPriority) => {
    const variants: Record<TaskPriority, string> = {
      urgent: 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400',
      high: 'bg-orange-100 text-orange-700 dark:bg-orange-900/20 dark:text-orange-400',
      medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400',
      low: 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400',
    };

    return (
      <Badge className={cn('text-xs', variants[priority])}>
        <Flag className="mr-1 h-3 w-3" />
        {priority}
      </Badge>
    );
  };

  return (
    <DashboardLayout>
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold">Tasks</h1>
              <p className="text-sm text-muted-foreground">Manage and organize your tasks</p>
            </div>
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="mr-2 h-4 w-4" />
              New Task
            </Button>
          </div>
        </div>

        {/* Filters and View Options */}
        <div className="border-b px-6 py-3">
          <div className="flex items-center justify-between gap-4">
            <div className="flex flex-1 items-center gap-4">
              {/* Search */}
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search tasks..."
                  className="pl-9"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              {/* Filters */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Filter className="mr-2 h-4 w-4" />
                    Filters
                    {(statusFilter !== 'all' || priorityFilter !== 'all') && (
                      <Badge variant="secondary" className="ml-2">
                        {[statusFilter !== 'all', priorityFilter !== 'all'].filter(Boolean).length}
                      </Badge>
                    )}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="w-56">
                  <DropdownMenuLabel>Status</DropdownMenuLabel>
                  <DropdownMenuCheckboxItem
                    checked={statusFilter === 'all'}
                    onCheckedChange={() => setStatusFilter('all')}
                  >
                    All Status
                  </DropdownMenuCheckboxItem>
                  {(['todo', 'in_progress', 'done', 'cancelled'] as const).map((status) => (
                    <DropdownMenuCheckboxItem
                      key={status}
                      checked={statusFilter === status}
                      onCheckedChange={() => setStatusFilter(status)}
                    >
                      {status.replace('_', ' ')}
                    </DropdownMenuCheckboxItem>
                  ))}
                  <DropdownMenuSeparator />
                  <DropdownMenuLabel>Priority</DropdownMenuLabel>
                  <DropdownMenuCheckboxItem
                    checked={priorityFilter === 'all'}
                    onCheckedChange={() => setPriorityFilter('all')}
                  >
                    All Priorities
                  </DropdownMenuCheckboxItem>
                  {(['urgent', 'high', 'medium', 'low'] as const).map((priority) => (
                    <DropdownMenuCheckboxItem
                      key={priority}
                      checked={priorityFilter === priority}
                      onCheckedChange={() => setPriorityFilter(priority)}
                    >
                      {priority}
                    </DropdownMenuCheckboxItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>

              {/* Sort */}
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="position">Manual order</SelectItem>
                  <SelectItem value="due_date">Due date</SelectItem>
                  <SelectItem value="priority">Priority</SelectItem>
                  <SelectItem value="created_at">Created date</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* View Mode */}
            <div className="flex items-center rounded-md border">
              <Button
                variant={viewMode === 'list' ? 'secondary' : 'ghost'}
                size="sm"
                className="rounded-none rounded-l-md"
                onClick={() => setViewMode('list')}
              >
                <List className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === 'board' ? 'secondary' : 'ghost'}
                size="sm"
                className="rounded-none border-x"
                onClick={() => setViewMode('board')}
              >
                <Kanban className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === 'calendar' ? 'secondary' : 'ghost'}
                size="sm"
                className="rounded-none rounded-r-md"
                onClick={() => setViewMode('calendar')}
              >
                <CalendarDays className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Bulk Actions */}
          {selectedTasks.length > 0 && (
            <div className="mt-3 flex items-center gap-4">
              <span className="text-sm text-muted-foreground">{selectedTasks.length} selected</span>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={handleBulkDelete}>
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </Button>
                <Button variant="outline" size="sm" disabled>
                  <Archive className="mr-2 h-4 w-4" />
                  Archive
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Task List */}
        <div className="flex-1 overflow-auto">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                <p className="mt-2 text-sm text-muted-foreground">Loading tasks...</p>
              </div>
            </div>
          ) : filteredTasks.length === 0 ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <Circle className="mx-auto h-12 w-12 text-muted-foreground" />
                <h3 className="mt-2 text-sm font-medium">No tasks found</h3>
                <p className="mt-1 text-sm text-muted-foreground">
                  {searchQuery || statusFilter !== 'all' || priorityFilter !== 'all'
                    ? 'Try adjusting your filters'
                    : 'Get started by creating a new task'}
                </p>
                {!searchQuery && statusFilter === 'all' && priorityFilter === 'all' && (
                  <Button className="mt-4" onClick={() => setShowCreateModal(true)}>
                    <Plus className="mr-2 h-4 w-4" />
                    Create Task
                  </Button>
                )}
              </div>
            </div>
          ) : viewMode === 'list' ? (
            <div className="divide-y">
              {/* Select All */}
              <div className="flex items-center gap-4 px-6 py-3 text-sm text-muted-foreground">
                <Checkbox
                  checked={selectedTasks.length === filteredTasks.length}
                  onCheckedChange={handleSelectAll}
                />
                <span>Select all</span>
              </div>

              {/* Task Items */}
              {filteredTasks.map((task) => (
                <div
                  key={task.id}
                  className={cn(
                    'group flex items-center gap-4 px-6 py-3 hover:bg-muted/50 cursor-pointer',
                    selectedTasks.includes(task.id) && 'bg-muted/50'
                  )}
                  onClick={() => router.push(`/tasks/${task.id}`)}
                >
                  <Checkbox
                    checked={selectedTasks.includes(task.id)}
                    onCheckedChange={() => handleSelectTask(task.id)}
                    onClick={(e) => e.stopPropagation()}
                  />

                  {getStatusIcon(task.status)}

                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={cn(
                          'font-medium',
                          task.status === 'done' && 'line-through text-muted-foreground'
                        )}
                      >
                        {task.title}
                      </span>
                      {task.tags.map((tag) => (
                        <Badge key={tag.id} variant="outline" className="text-xs">
                          {tag.name}
                        </Badge>
                      ))}
                    </div>
                    {task.description && (
                      <p className="text-sm text-muted-foreground line-clamp-1">
                        {task.description}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center gap-4">
                    {task.due_date && (
                      <div className="flex items-center gap-1 text-sm text-muted-foreground">
                        <Calendar className="h-4 w-4" />
                        {format(new Date(task.due_date), 'MMM d')}
                      </div>
                    )}

                    {getPriorityBadge(task.priority)}

                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="opacity-0 group-hover:opacity-100"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          onClick={(e) => {
                            e.stopPropagation();
                            router.push(`/tasks/${task.id}`);
                          }}
                        >
                          <Edit className="mr-2 h-4 w-4" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={(e) => e.stopPropagation()}>
                          <Copy className="mr-2 h-4 w-4" />
                          Duplicate
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={(e) => e.stopPropagation()}>
                          <Share2 className="mr-2 h-4 w-4" />
                          Share
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={async (e) => {
                            e.stopPropagation();
                            try {
                              await TasksService.deleteTask(task.id);
                              toast({
                                title: 'Success',
                                description: 'Task deleted successfully',
                              });
                              fetchTasks();
                            } catch (error) {
                              toast({
                                title: 'Error',
                                description: 'Failed to delete task',
                                variant: 'destructive',
                              });
                            }
                          }}
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              ))}
            </div>
          ) : viewMode === 'board' ? (
            <div className="flex gap-4 p-6 overflow-x-auto">
              {/* Board View - Kanban Style */}
              {(['todo', 'in_progress', 'done'] as const).map((status) => {
                const columnTasks = filteredTasks.filter((task) => task.status === status);
                const columnTitle = {
                  todo: 'To Do',
                  in_progress: 'In Progress',
                  done: 'Done',
                }[status];

                return (
                  <div key={status} className="flex-1 min-w-[300px]">
                    <div className="mb-3 flex items-center justify-between">
                      <h3 className="font-medium flex items-center gap-2">
                        {getStatusIcon(status)}
                        {columnTitle}
                        <span className="text-sm text-muted-foreground">
                          ({columnTasks.length})
                        </span>
                      </h3>
                    </div>

                    <div className="space-y-2">
                      {columnTasks.map((task) => (
                        <div
                          key={task.id}
                          className="group rounded-lg border bg-card p-3 hover:shadow-md transition-shadow cursor-pointer"
                          onClick={() => router.push(`/tasks/${task.id}`)}
                        >
                          <div className="flex items-start justify-between mb-2">
                            <h4 className="font-medium text-sm line-clamp-2">{task.title}</h4>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  <MoreHorizontal className="h-3 w-3" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    router.push(`/tasks/${task.id}`);
                                  }}
                                >
                                  <Edit className="mr-2 h-4 w-4" />
                                  Edit
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={(e) => e.stopPropagation()}>
                                  <Copy className="mr-2 h-4 w-4" />
                                  Duplicate
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  className="text-destructive"
                                  onClick={async (e) => {
                                    e.stopPropagation();
                                    try {
                                      await TasksService.deleteTask(task.id);
                                      toast({
                                        title: 'Success',
                                        description: 'Task deleted successfully',
                                      });
                                      fetchTasks();
                                    } catch (error) {
                                      toast({
                                        title: 'Error',
                                        description: 'Failed to delete task',
                                        variant: 'destructive',
                                      });
                                    }
                                  }}
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  Delete
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </div>

                          {task.description && (
                            <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
                              {task.description}
                            </p>
                          )}

                          <div className="flex items-center gap-2 flex-wrap">
                            {getPriorityBadge(task.priority)}

                            {task.due_date && (
                              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                <Calendar className="h-3 w-3" />
                                {format(new Date(task.due_date), 'MMM d')}
                              </div>
                            )}

                            {task.tags.map((tag) => (
                              <Badge key={tag.id} variant="outline" className="text-xs py-0 px-1">
                                {tag.name}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      ))}

                      {columnTasks.length === 0 && (
                        <div className="rounded-lg border-2 border-dashed p-8 text-center">
                          <p className="text-sm text-muted-foreground">No tasks</p>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : viewMode === 'calendar' ? (
            <div className="p-6">
              <TaskCalendar
                tasks={filteredTasks}
                onTaskClick={(task) => router.push(`/tasks/${task.id}`)}
              />
            </div>
          ) : null}
        </div>

        {/* Create Task Modal */}
        <CreateTaskModal
          open={showCreateModal}
          onOpenChange={setShowCreateModal}
          onSuccess={() => {
            fetchTasks();
            setShowCreateModal(false);
          }}
        />
      </div>
    </DashboardLayout>
  );
}
