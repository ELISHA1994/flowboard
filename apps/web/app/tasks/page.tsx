'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
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
  FolderOpen,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Task, TaskStatus, TaskPriority, CreateTaskRequest } from '@/lib/api/tasks';
import { Project, ProjectsService } from '@/lib/api/projects';
import { Category, CategoriesService } from '@/lib/api/categories';
import { Tag, TagsService } from '@/lib/api/tags';
import { CreateTaskModal } from '@/components/tasks/create-task-modal';
import { TaskCalendar } from '@/components/tasks/task-calendar';
import { DashboardLayout } from '@/components/layouts/dashboard-layout';
import { format } from 'date-fns';
import { useToast } from '@/hooks/use-toast';
import { useCategoriesQuery } from '@/hooks/use-categories-query';
import { useTagsQuery } from '@/hooks/use-tags-query';
import { Hash, Folder } from 'lucide-react';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  useTasksQuery,
  useBulkUpdateTasksMutation,
  useBulkDeleteTasksMutation,
  useDeleteTaskMutation,
  useCreateTaskMutation,
} from '@/hooks/use-tasks-query';
import { EditTaskModal } from '@/components/tasks/edit-task-modal';
import { ShareTaskModal } from '@/components/tasks/share-task-modal';
import { AdvancedFiltersModal, AdvancedFilters } from '@/components/tasks/advanced-filters-modal';
import { SavedSearches } from '@/components/tasks/saved-searches';
import { BulkOperationsModal, BulkOperation } from '@/components/tasks/bulk-operations-modal';
import { TaskDetailModal } from '@/components/tasks/task-detail-modal';

type ViewMode = 'list' | 'board' | 'calendar';

export default function TasksPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [selectedTasks, setSelectedTasks] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<TaskStatus | 'all'>('all');
  const [priorityFilter, setPriorityFilter] = useState<TaskPriority | 'all'>('all');
  const [projectFilter, setProjectFilter] = useState<string | 'all'>('all');
  const [projects, setProjects] = useState<Project[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [categoriesOpen, setCategoriesOpen] = useState(false);
  const [tagsOpen, setTagsOpen] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [sortBy, setSortBy] = useState<string>('position');
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [taskToShare, setTaskToShare] = useState<Task | null>(null);
  const [advancedFiltersOpen, setAdvancedFiltersOpen] = useState(false);
  const [bulkOperationsOpen, setBulkOperationsOpen] = useState(false);
  const [taskDetailModalOpen, setTaskDetailModalOpen] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [advancedFilters, setAdvancedFilters] = useState<AdvancedFilters>({
    searchQuery: '',
    status: 'all',
    priority: 'all',
    projectId: 'all',
    categoryIds: [],
    tagIds: [],
    assignedToId: 'all',
    sortBy: 'created_at',
    sortOrder: 'desc',
  });

  // Get project_id from URL params
  const projectIdFromUrl = searchParams.get('project_id');

  // Initialize project filter from URL
  useEffect(() => {
    if (projectIdFromUrl) {
      setProjectFilter(projectIdFromUrl);
    }
  }, [projectIdFromUrl]);

  // Keep advancedFilters in sync with individual filters
  useEffect(() => {
    setAdvancedFilters((prev) => ({
      ...prev,
      searchQuery: searchQuery,
      status: statusFilter,
      priority: priorityFilter,
      projectId: projectFilter,
      categoryIds: selectedCategories,
      tagIds: selectedTags,
      sortBy: sortBy,
    }));
  }, [
    searchQuery,
    statusFilter,
    priorityFilter,
    projectFilter,
    selectedCategories,
    selectedTags,
    sortBy,
  ]);

  // Fetch projects for filtering
  useEffect(() => {
    const fetchProjects = async () => {
      try {
        setLoadingProjects(true);
        const projectList = await ProjectsService.getProjects();
        setProjects(projectList);
      } catch (error) {
        console.error('Failed to fetch projects:', error);
      } finally {
        setLoadingProjects(false);
      }
    };
    fetchProjects();
  }, []);

  // Fetch categories and tags
  const { data: categories = [] } = useCategoriesQuery();
  const { data: tags = [] } = useTagsQuery();

  const bulkUpdateMutation = useBulkUpdateTasksMutation();
  const bulkDeleteMutation = useBulkDeleteTasksMutation();
  const deleteTaskMutation = useDeleteTaskMutation();
  const createTaskMutation = useCreateTaskMutation();

  // Create query params from current filter states to avoid infinite loops
  const taskQueryParams = useMemo(
    () => ({
      status: statusFilter === 'all' ? undefined : statusFilter,
      priority: priorityFilter === 'all' ? undefined : priorityFilter,
      project_id: projectFilter === 'all' ? undefined : projectFilter,
      category_ids: selectedCategories?.length > 0 ? selectedCategories : undefined,
      tag_ids: selectedTags?.length > 0 ? selectedTags : undefined,
      sort_by: sortBy === 'position' ? 'created_at' : (sortBy as any),
      limit: 100,
    }),
    [statusFilter, priorityFilter, projectFilter, selectedCategories, selectedTags, sortBy]
  );

  // Apply advanced filters
  const handleApplyAdvancedFilters = (filters: AdvancedFilters) => {
    setAdvancedFilters(filters);
    setSearchQuery(filters.searchQuery || '');
    setStatusFilter(filters.status || 'all');
    setPriorityFilter(filters.priority || 'all');
    setProjectFilter(filters.projectId || 'all');
    setSelectedCategories(filters.categoryIds || []);
    setSelectedTags(filters.tagIds || []);
    setSortBy(filters.sortBy || 'created_at');
  };

  // Fetch tasks using React Query
  const { data: tasksData, isLoading, error } = useTasksQuery(taskQueryParams);

  const tasks = tasksData?.tasks || [];

  // Show error if fetch failed
  useEffect(() => {
    if (error) {
      console.error('Failed to fetch tasks:', error);
      toast({
        title: 'Error',
        description: 'Failed to load tasks. Please try again.',
        variant: 'destructive',
      });
    }
  }, [error, toast]);

  // Filter tasks based on search and exclude subtasks (following UX best practices)
  const filteredTasks = tasks.filter(
    (task) =>
      // Exclude subtasks - only show parent tasks in main list
      !task.parent_task_id &&
      // Apply search filter
      (advancedFilters.searchQuery
        ? task.title.toLowerCase().includes(advancedFilters.searchQuery.toLowerCase()) ||
          task.description?.toLowerCase().includes(advancedFilters.searchQuery.toLowerCase())
        : true)
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
  const handleBulkDelete = () => {
    if (selectedTasks.length === 0) return;

    bulkDeleteMutation.mutate(selectedTasks, {
      onSuccess: () => {
        setSelectedTasks([]);
      },
    });
  };

  const handleBulkOperations = (operations: BulkOperation[]) => {
    if (selectedTasks.length === 0 || operations.length === 0) return;

    // Convert operations to UpdateTaskRequest
    const updateData: any = {};
    operations.forEach((op) => {
      updateData[op.field] = op.value;
    });

    bulkUpdateMutation.mutate(
      { ids: selectedTasks, data: updateData },
      {
        onSuccess: () => {
          setSelectedTasks([]);
          setBulkOperationsOpen(false);
        },
      }
    );
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
            <Button variant="primary" onClick={() => setShowCreateModal(true)}>
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
              <Button variant="outline" size="sm" onClick={() => setAdvancedFiltersOpen(true)}>
                <Filter className="mr-2 h-4 w-4" />
                Advanced Filters
                {(() => {
                  let count = 0;
                  if (advancedFilters.searchQuery) count++;
                  if (advancedFilters.status && advancedFilters.status !== 'all') count++;
                  if (advancedFilters.priority && advancedFilters.priority !== 'all') count++;
                  if (advancedFilters.projectId && advancedFilters.projectId !== 'all') count++;
                  if (advancedFilters.categoryIds && advancedFilters.categoryIds.length > 0)
                    count++;
                  if (advancedFilters.tagIds && advancedFilters.tagIds.length > 0) count++;
                  if (advancedFilters.assignedToId && advancedFilters.assignedToId !== 'all')
                    count++;
                  if (advancedFilters.dueDateFrom || advancedFilters.dueDateTo) count++;
                  if (advancedFilters.createdDateFrom || advancedFilters.createdDateTo) count++;
                  return (
                    count > 0 && (
                      <Badge variant="secondary" className="ml-2">
                        {count}
                      </Badge>
                    )
                  );
                })()}
              </Button>

              {/* Saved Searches */}
              <SavedSearches
                onApplySearch={handleApplyAdvancedFilters}
                currentFilters={advancedFilters}
              />

              {/* Quick Filters */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm">
                    <ChevronDown className="mr-2 h-4 w-4" />
                    Quick Filters
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="w-56">
                  <DropdownMenuLabel>Project</DropdownMenuLabel>
                  <DropdownMenuCheckboxItem
                    checked={projectFilter === 'all'}
                    onCheckedChange={() => setProjectFilter('all')}
                  >
                    All Projects
                  </DropdownMenuCheckboxItem>
                  {projects.map((project) => (
                    <DropdownMenuCheckboxItem
                      key={project.id}
                      checked={projectFilter === project.id}
                      onCheckedChange={() => setProjectFilter(project.id)}
                    >
                      <div className="flex items-center gap-2">
                        <div
                          className="h-3 w-3 rounded-full"
                          style={{ backgroundColor: project.color || '#6366f1' }}
                        />
                        {project.name}
                      </div>
                    </DropdownMenuCheckboxItem>
                  ))}
                  <DropdownMenuSeparator />
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

              {/* Category Filter */}
              <Popover open={categoriesOpen} onOpenChange={setCategoriesOpen}>
                <PopoverTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Folder className="mr-2 h-4 w-4" />
                    Categories
                    {selectedCategories.length > 0 && (
                      <Badge variant="secondary" className="ml-2">
                        {selectedCategories.length}
                      </Badge>
                    )}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-56 p-0" align="start">
                  <div className="p-2 border-b">
                    <p className="text-sm font-medium">Filter by Categories</p>
                  </div>
                  <ScrollArea className="h-[200px]">
                    {categories.map((category) => (
                      <div
                        key={category.id}
                        className="flex items-center space-x-2 px-2 py-1.5 hover:bg-accent cursor-pointer"
                        onClick={() => {
                          if (selectedCategories.includes(category.id)) {
                            setSelectedCategories(
                              selectedCategories.filter((id) => id !== category.id)
                            );
                          } else {
                            setSelectedCategories([...selectedCategories, category.id]);
                          }
                        }}
                      >
                        <Checkbox
                          checked={selectedCategories.includes(category.id)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setSelectedCategories([...selectedCategories, category.id]);
                            } else {
                              setSelectedCategories(
                                selectedCategories.filter((id) => id !== category.id)
                              );
                            }
                          }}
                          onClick={(e) => e.stopPropagation()}
                        />
                        <div className="flex items-center gap-2 flex-1">
                          <div
                            className="h-6 w-6 rounded flex items-center justify-center text-xs"
                            style={{
                              backgroundColor:
                                CategoriesService.formatCategoryColor(category.color) + '20',
                              color: CategoriesService.formatCategoryColor(category.color),
                            }}
                          >
                            {CategoriesService.formatCategoryIcon(category.icon)}
                          </div>
                          <span className="text-sm">{category.name}</span>
                        </div>
                      </div>
                    ))}
                  </ScrollArea>
                  {selectedCategories.length > 0 && (
                    <div className="p-2 border-t">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="w-full"
                        onClick={() => setSelectedCategories([])}
                      >
                        Clear selection
                      </Button>
                    </div>
                  )}
                </PopoverContent>
              </Popover>

              {/* Tag Filter */}
              <Popover open={tagsOpen} onOpenChange={setTagsOpen}>
                <PopoverTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Hash className="mr-2 h-4 w-4" />
                    Tags
                    {selectedTags.length > 0 && (
                      <Badge variant="secondary" className="ml-2">
                        {selectedTags.length}
                      </Badge>
                    )}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-56 p-0" align="start">
                  <div className="p-2 border-b">
                    <p className="text-sm font-medium">Filter by Tags</p>
                  </div>
                  <ScrollArea className="h-[200px]">
                    {tags.map((tag) => (
                      <div
                        key={tag.id}
                        className="flex items-center space-x-2 px-2 py-1.5 hover:bg-accent cursor-pointer"
                        onClick={() => {
                          if (selectedTags.includes(tag.id)) {
                            setSelectedTags(selectedTags.filter((id) => id !== tag.id));
                          } else {
                            setSelectedTags([...selectedTags, tag.id]);
                          }
                        }}
                      >
                        <Checkbox
                          checked={selectedTags.includes(tag.id)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setSelectedTags([...selectedTags, tag.id]);
                            } else {
                              setSelectedTags(selectedTags.filter((id) => id !== tag.id));
                            }
                          }}
                          onClick={(e) => e.stopPropagation()}
                        />
                        <Badge
                          variant="outline"
                          className="text-xs flex-1"
                          style={{
                            backgroundColor: TagsService.formatTagColor(tag.color) + '20',
                            color: TagsService.formatTagColor(tag.color),
                            borderColor: TagsService.formatTagColor(tag.color),
                          }}
                        >
                          <Hash className="h-3 w-3 mr-1" />
                          {tag.name}
                        </Badge>
                      </div>
                    ))}
                  </ScrollArea>
                  {selectedTags.length > 0 && (
                    <div className="p-2 border-t">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="w-full"
                        onClick={() => setSelectedTags([])}
                      >
                        Clear selection
                      </Button>
                    </div>
                  )}
                </PopoverContent>
              </Popover>

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
                <Button variant="outline" size="sm" onClick={() => setBulkOperationsOpen(true)}>
                  <Edit className="mr-2 h-4 w-4" />
                  Edit {selectedTasks.length} Task{selectedTasks.length !== 1 ? 's' : ''}
                </Button>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm">
                      <MoreHorizontal className="mr-2 h-4 w-4" />
                      More Actions
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start">
                    <DropdownMenuItem
                      onClick={() =>
                        handleBulkOperations([
                          { field: 'status', value: 'done', label: 'Status: Done' },
                        ])
                      }
                    >
                      <CheckCircle2 className="mr-2 h-4 w-4" />
                      Mark as Done
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() =>
                        handleBulkOperations([
                          { field: 'status', value: 'in_progress', label: 'Status: In Progress' },
                        ])
                      }
                    >
                      <Clock className="mr-2 h-4 w-4" />
                      Mark as In Progress
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      onClick={() =>
                        handleBulkOperations([
                          { field: 'priority', value: 'urgent', label: 'Priority: Urgent' },
                        ])
                      }
                    >
                      <Flag className="mr-2 h-4 w-4 text-red-600" />
                      Set Priority to Urgent
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() =>
                        handleBulkOperations([
                          { field: 'priority', value: 'high', label: 'Priority: High' },
                        ])
                      }
                    >
                      <Flag className="mr-2 h-4 w-4 text-orange-600" />
                      Set Priority to High
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={handleBulkDelete} className="text-destructive">
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete Selected
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          )}
        </div>

        {/* Task List */}
        <div className="flex-1 overflow-auto">
          {isLoading ? (
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
                  {searchQuery ||
                  statusFilter !== 'all' ||
                  priorityFilter !== 'all' ||
                  projectFilter !== 'all' ||
                  selectedCategories.length > 0 ||
                  selectedTags.length > 0
                    ? 'Try adjusting your filters'
                    : 'Get started by creating a new task'}
                </p>
                {!searchQuery &&
                  statusFilter === 'all' &&
                  priorityFilter === 'all' &&
                  projectFilter === 'all' &&
                  selectedCategories.length === 0 &&
                  selectedTags.length === 0 && (
                    <Button
                      variant="primary"
                      className="mt-4"
                      onClick={() => setShowCreateModal(true)}
                    >
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
                  onClick={() => {
                    setSelectedTaskId(task.id);
                    setTaskDetailModalOpen(true);
                  }}
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
                            setSelectedTaskId(task.id);
                            setTaskDetailModalOpen(true);
                          }}
                        >
                          <Edit className="mr-2 h-4 w-4" />
                          View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={(e) => {
                            e.stopPropagation();
                            const duplicateData: CreateTaskRequest = {
                              title: `${task.title} (Copy)`,
                              description: task.description,
                              status: task.status,
                              priority: task.priority,
                              due_date: task.due_date,
                              start_date: task.start_date,
                              estimated_hours: task.estimated_hours,
                              assigned_to_id: task.assigned_to_id,
                              project_id: task.project_id,
                              parent_task_id: task.parent_task_id,
                              tag_ids: task.tags.map((tag) => tag.id),
                              category_ids: task.categories.map((cat) => cat.id),
                            };
                            createTaskMutation.mutate(duplicateData);
                          }}
                        >
                          <Copy className="mr-2 h-4 w-4" />
                          Duplicate
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={(e) => {
                            e.stopPropagation();
                            setTaskToShare(task);
                            setShareModalOpen(true);
                          }}
                        >
                          <Share2 className="mr-2 h-4 w-4" />
                          Share
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteTaskMutation.mutate(task.id);
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
                          onClick={() => {
                            setSelectedTaskId(task.id);
                            setTaskDetailModalOpen(true);
                          }}
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
                                    setSelectedTaskId(task.id);
                                    setTaskDetailModalOpen(true);
                                  }}
                                >
                                  <Edit className="mr-2 h-4 w-4" />
                                  View Details
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    const duplicateData: CreateTaskRequest = {
                                      title: `${task.title} (Copy)`,
                                      description: task.description,
                                      status: task.status,
                                      priority: task.priority,
                                      due_date: task.due_date,
                                      start_date: task.start_date,
                                      estimated_hours: task.estimated_hours,
                                      assigned_to_id: task.assigned_to_id,
                                      project_id: task.project_id,
                                      parent_task_id: task.parent_task_id,
                                      tag_ids: task.tags.map((tag) => tag.id),
                                      category_ids: task.categories.map((cat) => cat.id),
                                    };
                                    createTaskMutation.mutate(duplicateData);
                                  }}
                                >
                                  <Copy className="mr-2 h-4 w-4" />
                                  Duplicate
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  className="text-destructive"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    deleteTaskMutation.mutate(task.id);
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
                onTaskClick={(task) => {
                  setSelectedTaskId(task.id);
                  setTaskDetailModalOpen(true);
                }}
              />
            </div>
          ) : null}
        </div>

        {/* Create Task Modal */}
        <CreateTaskModal
          open={showCreateModal}
          onOpenChange={setShowCreateModal}
          defaultProjectId={projectFilter !== 'all' ? projectFilter : undefined}
          onTaskCreated={() => {
            // React Query will automatically refetch
            setShowCreateModal(false);
          }}
        />

        {/* Edit Task Modal */}
        <EditTaskModal
          open={editModalOpen}
          onOpenChange={setEditModalOpen}
          task={selectedTask}
          onTaskUpdated={() => {
            // React Query will automatically refetch
            setSelectedTask(null);
          }}
        />

        {/* Share Task Modal */}
        <ShareTaskModal open={shareModalOpen} onOpenChange={setShareModalOpen} task={taskToShare} />

        {/* Advanced Filters Modal */}
        <AdvancedFiltersModal
          open={advancedFiltersOpen}
          onOpenChange={setAdvancedFiltersOpen}
          filters={advancedFilters}
          onApplyFilters={handleApplyAdvancedFilters}
          projects={projects}
          categories={categories}
          tags={tags}
          users={[]} // TODO: Add users list when user management is implemented
        />

        {/* Bulk Operations Modal */}
        <BulkOperationsModal
          open={bulkOperationsOpen}
          onOpenChange={setBulkOperationsOpen}
          selectedCount={selectedTasks.length}
          onApplyOperations={handleBulkOperations}
          projects={projects}
          categories={categories}
          tags={tags}
          users={[]} // TODO: Add users list when user management is implemented
        />

        {/* Task Detail Modal */}
        <TaskDetailModal
          open={taskDetailModalOpen}
          onOpenChange={setTaskDetailModalOpen}
          taskId={selectedTaskId}
          onTaskUpdated={() => {
            // React Query will automatically refetch
          }}
          onNavigateToTask={(taskId) => {
            setTaskDetailModalOpen(false);
            router.push(`/tasks/${taskId}`);
          }}
        />
      </div>
    </DashboardLayout>
  );
}
