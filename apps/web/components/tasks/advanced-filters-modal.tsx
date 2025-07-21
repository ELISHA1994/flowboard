'use client';

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';
import { CalendarIcon, X } from 'lucide-react';
import { TaskStatus, TaskPriority } from '@/lib/api/tasks';
import { Project } from '@/lib/api/projects';
import { Category, CategoriesService } from '@/lib/api/categories';
import { Tag, TagsService } from '@/lib/api/tags';

export interface AdvancedFilters {
  searchQuery?: string;
  status?: TaskStatus | 'all';
  priority?: TaskPriority | 'all';
  projectId?: string | 'all';
  categoryIds?: string[];
  tagIds?: string[];
  assignedToId?: string | 'all';
  dueDateFrom?: Date;
  dueDateTo?: Date;
  createdDateFrom?: Date;
  createdDateTo?: Date;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

interface AdvancedFiltersModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  filters: AdvancedFilters;
  onApplyFilters: (filters: AdvancedFilters) => void;
  projects: Project[];
  categories: Category[];
  tags: Tag[];
  users?: Array<{ id: string; username: string; email: string }>;
}

export function AdvancedFiltersModal({
  open,
  onOpenChange,
  filters,
  onApplyFilters,
  projects,
  categories,
  tags,
  users = [],
}: AdvancedFiltersModalProps) {
  const [localFilters, setLocalFilters] = useState<AdvancedFilters>(filters);

  const handleReset = () => {
    setLocalFilters({
      searchQuery: '',
      status: 'all',
      priority: 'all',
      projectId: 'all',
      categoryIds: [],
      tagIds: [],
      assignedToId: 'all',
      dueDateFrom: undefined,
      dueDateTo: undefined,
      createdDateFrom: undefined,
      createdDateTo: undefined,
      sortBy: 'created_at',
      sortOrder: 'desc',
    });
  };

  const handleApply = () => {
    onApplyFilters(localFilters);
    onOpenChange(false);
  };

  const activeFilterCount = () => {
    let count = 0;
    if (localFilters.searchQuery) count++;
    if (localFilters.status && localFilters.status !== 'all') count++;
    if (localFilters.priority && localFilters.priority !== 'all') count++;
    if (localFilters.projectId && localFilters.projectId !== 'all') count++;
    if (localFilters.categoryIds && localFilters.categoryIds.length > 0) count++;
    if (localFilters.tagIds && localFilters.tagIds.length > 0) count++;
    if (localFilters.assignedToId && localFilters.assignedToId !== 'all') count++;
    if (localFilters.dueDateFrom || localFilters.dueDateTo) count++;
    if (localFilters.createdDateFrom || localFilters.createdDateTo) count++;
    return count;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle>Advanced Filters</DialogTitle>
          <DialogDescription>
            Refine your task search with advanced filtering options
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="h-[500px] pr-4">
          <div className="space-y-6">
            {/* Search Query */}
            <div className="space-y-2">
              <Label htmlFor="search">Search</Label>
              <Input
                id="search"
                placeholder="Search in title and description..."
                value={localFilters.searchQuery || ''}
                onChange={(e) => setLocalFilters({ ...localFilters, searchQuery: e.target.value })}
              />
            </div>

            {/* Status and Priority */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="status">Status</Label>
                <Select
                  value={localFilters.status || 'all'}
                  onValueChange={(value) =>
                    setLocalFilters({ ...localFilters, status: value as any })
                  }
                >
                  <SelectTrigger id="status">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="todo">To Do</SelectItem>
                    <SelectItem value="in_progress">In Progress</SelectItem>
                    <SelectItem value="done">Done</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="priority">Priority</Label>
                <Select
                  value={localFilters.priority || 'all'}
                  onValueChange={(value) =>
                    setLocalFilters({ ...localFilters, priority: value as any })
                  }
                >
                  <SelectTrigger id="priority">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Priorities</SelectItem>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="urgent">Urgent</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Project and Assigned To */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="project">Project</Label>
                <Select
                  value={localFilters.projectId || 'all'}
                  onValueChange={(value) => setLocalFilters({ ...localFilters, projectId: value })}
                >
                  <SelectTrigger id="project">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Projects</SelectItem>
                    {projects.map((project) => (
                      <SelectItem key={project.id} value={project.id}>
                        <div className="flex items-center gap-2">
                          <div
                            className="h-3 w-3 rounded-full"
                            style={{ backgroundColor: project.color || '#6366f1' }}
                          />
                          {project.name}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="assigned">Assigned To</Label>
                <Select
                  value={localFilters.assignedToId || 'all'}
                  onValueChange={(value) =>
                    setLocalFilters({ ...localFilters, assignedToId: value })
                  }
                >
                  <SelectTrigger id="assigned">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Anyone</SelectItem>
                    <SelectItem value="unassigned">Unassigned</SelectItem>
                    {users.map((user) => (
                      <SelectItem key={user.id} value={user.id}>
                        {user.username}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Categories */}
            <div className="space-y-2">
              <Label>Categories</Label>
              <div className="border rounded-lg p-3">
                <ScrollArea className="h-[120px]">
                  <div className="space-y-2">
                    {categories.map((category) => (
                      <div key={category.id} className="flex items-center space-x-2">
                        <Checkbox
                          id={`category-${category.id}`}
                          checked={localFilters.categoryIds?.includes(category.id)}
                          onCheckedChange={(checked) => {
                            const categoryIds = localFilters.categoryIds || [];
                            if (checked) {
                              setLocalFilters({
                                ...localFilters,
                                categoryIds: [...categoryIds, category.id],
                              });
                            } else {
                              setLocalFilters({
                                ...localFilters,
                                categoryIds: categoryIds.filter((id) => id !== category.id),
                              });
                            }
                          }}
                        />
                        <label
                          htmlFor={`category-${category.id}`}
                          className="flex items-center gap-2 cursor-pointer flex-1"
                        >
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
                          {category.name}
                        </label>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            </div>

            {/* Tags */}
            <div className="space-y-2">
              <Label>Tags</Label>
              <div className="border rounded-lg p-3">
                <ScrollArea className="h-[120px]">
                  <div className="flex flex-wrap gap-2">
                    {tags.map((tag) => (
                      <Badge
                        key={tag.id}
                        variant={localFilters.tagIds?.includes(tag.id) ? 'default' : 'outline'}
                        className="cursor-pointer"
                        style={{
                          backgroundColor: localFilters.tagIds?.includes(tag.id)
                            ? TagsService.formatTagColor(tag.color)
                            : TagsService.formatTagColor(tag.color) + '20',
                          color: localFilters.tagIds?.includes(tag.id)
                            ? 'white'
                            : TagsService.formatTagColor(tag.color),
                          borderColor: TagsService.formatTagColor(tag.color),
                        }}
                        onClick={() => {
                          const tagIds = localFilters.tagIds || [];
                          if (tagIds.includes(tag.id)) {
                            setLocalFilters({
                              ...localFilters,
                              tagIds: tagIds.filter((id) => id !== tag.id),
                            });
                          } else {
                            setLocalFilters({
                              ...localFilters,
                              tagIds: [...tagIds, tag.id],
                            });
                          }
                        }}
                      >
                        #{tag.name}
                      </Badge>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            </div>

            {/* Date Filters */}
            <div className="space-y-4">
              <div>
                <Label>Due Date Range</Label>
                <div className="grid grid-cols-2 gap-2 mt-2">
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className={cn(
                          'justify-start text-left font-normal',
                          !localFilters.dueDateFrom && 'text-muted-foreground'
                        )}
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {localFilters.dueDateFrom ? (
                          format(localFilters.dueDateFrom, 'PPP')
                        ) : (
                          <span>From date</span>
                        )}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <Calendar
                        mode="single"
                        selected={localFilters.dueDateFrom}
                        onSelect={(date) => setLocalFilters({ ...localFilters, dueDateFrom: date })}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>

                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className={cn(
                          'justify-start text-left font-normal',
                          !localFilters.dueDateTo && 'text-muted-foreground'
                        )}
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {localFilters.dueDateTo ? (
                          format(localFilters.dueDateTo, 'PPP')
                        ) : (
                          <span>To date</span>
                        )}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <Calendar
                        mode="single"
                        selected={localFilters.dueDateTo}
                        onSelect={(date) => setLocalFilters({ ...localFilters, dueDateTo: date })}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>
              </div>

              <div>
                <Label>Created Date Range</Label>
                <div className="grid grid-cols-2 gap-2 mt-2">
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className={cn(
                          'justify-start text-left font-normal',
                          !localFilters.createdDateFrom && 'text-muted-foreground'
                        )}
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {localFilters.createdDateFrom ? (
                          format(localFilters.createdDateFrom, 'PPP')
                        ) : (
                          <span>From date</span>
                        )}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <Calendar
                        mode="single"
                        selected={localFilters.createdDateFrom}
                        onSelect={(date) =>
                          setLocalFilters({ ...localFilters, createdDateFrom: date })
                        }
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>

                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className={cn(
                          'justify-start text-left font-normal',
                          !localFilters.createdDateTo && 'text-muted-foreground'
                        )}
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {localFilters.createdDateTo ? (
                          format(localFilters.createdDateTo, 'PPP')
                        ) : (
                          <span>To date</span>
                        )}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <Calendar
                        mode="single"
                        selected={localFilters.createdDateTo}
                        onSelect={(date) =>
                          setLocalFilters({ ...localFilters, createdDateTo: date })
                        }
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>
              </div>
            </div>

            {/* Sort Options */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="sortBy">Sort By</Label>
                <Select
                  value={localFilters.sortBy || 'created_at'}
                  onValueChange={(value) => setLocalFilters({ ...localFilters, sortBy: value })}
                >
                  <SelectTrigger id="sortBy">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="created_at">Created Date</SelectItem>
                    <SelectItem value="updated_at">Updated Date</SelectItem>
                    <SelectItem value="due_date">Due Date</SelectItem>
                    <SelectItem value="priority">Priority</SelectItem>
                    <SelectItem value="title">Title</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="sortOrder">Sort Order</Label>
                <Select
                  value={localFilters.sortOrder || 'desc'}
                  onValueChange={(value) =>
                    setLocalFilters({ ...localFilters, sortOrder: value as 'asc' | 'desc' })
                  }
                >
                  <SelectTrigger id="sortOrder">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="desc">Descending</SelectItem>
                    <SelectItem value="asc">Ascending</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        </ScrollArea>

        <DialogFooter className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={handleReset}>
              Reset All
            </Button>
            {activeFilterCount() > 0 && (
              <Badge variant="secondary">
                {activeFilterCount()} active filter{activeFilterCount() > 1 ? 's' : ''}
              </Badge>
            )}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button onClick={handleApply}>Apply Filters</Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
