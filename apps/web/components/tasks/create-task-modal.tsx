'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, Loader2, FolderOpen } from 'lucide-react';
import { CreateTaskRequest } from '@/lib/api/tasks';
import { useCreateTaskMutation } from '@/hooks/use-tasks-query';
import { format } from 'date-fns';
import { Project, ProjectsService } from '@/lib/api/projects';
import { Category, CategoriesService } from '@/lib/api/categories';
import { Tag, TagsService } from '@/lib/api/tags';
import { useCategoriesQuery } from '@/hooks/use-categories-query';
import { useTagsQuery } from '@/hooks/use-tags-query';
import { Badge } from '@/components/ui/badge';
import { Hash, Folder } from 'lucide-react';
import { Checkbox } from '@/components/ui/checkbox';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

interface CreateTaskModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTaskCreated?: () => void;
  defaultProjectId?: string;
}

export function CreateTaskModal({
  open,
  onOpenChange,
  onTaskCreated,
  defaultProjectId,
}: CreateTaskModalProps) {
  const router = useRouter();
  const createTaskMutation = useCreateTaskMutation();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(false);

  // Fetch categories and tags
  const { data: categories = [] } = useCategoriesQuery();
  const { data: tags = [] } = useTagsQuery();

  // State for selected categories and tags
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [categoriesOpen, setCategoriesOpen] = useState(false);
  const [tagsOpen, setTagsOpen] = useState(false);

  const [formData, setFormData] = useState<CreateTaskRequest>({
    title: '',
    description: '',
    status: 'todo',
    priority: 'medium',
    due_date: '',
    start_date: '',
    estimated_hours: undefined,
    project_id: defaultProjectId,
    category_ids: [],
    tag_ids: [],
  });

  // Fetch projects when modal opens
  useEffect(() => {
    if (open) {
      fetchProjects();
    }
  }, [open]);

  // Update project_id when defaultProjectId changes
  useEffect(() => {
    if (defaultProjectId) {
      setFormData((prev) => ({ ...prev, project_id: defaultProjectId }));
    }
  }, [defaultProjectId]);

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.title.trim()) {
      return;
    }

    // Prepare the data - convert empty strings to undefined
    const taskData: CreateTaskRequest = {
      ...formData,
      description: formData.description || undefined,
      due_date: formData.due_date || undefined,
      start_date: formData.start_date || undefined,
      estimated_hours: formData.estimated_hours || undefined,
      category_ids: selectedCategories,
      tag_ids: selectedTags,
    };

    createTaskMutation.mutate(taskData, {
      onSuccess: () => {
        // Reset form
        setFormData({
          title: '',
          description: '',
          status: 'todo',
          priority: 'medium',
          due_date: '',
          start_date: '',
          estimated_hours: undefined,
          project_id: defaultProjectId,
          category_ids: [],
          tag_ids: [],
        });
        setSelectedCategories([]);
        setSelectedTags([]);

        // Close modal
        onOpenChange(false);

        // Notify parent component (optional now since React Query handles updates)
        if (onTaskCreated) {
          onTaskCreated();
        }
      },
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[525px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Create New Task</DialogTitle>
            <DialogDescription>
              Add a new task to your list. Fill in the details below.
            </DialogDescription>
          </DialogHeader>

          {createTaskMutation.error && (
            <Alert variant="destructive" className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {createTaskMutation.error instanceof Error
                  ? createTaskMutation.error.message
                  : 'Failed to create task'}
              </AlertDescription>
            </Alert>
          )}

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="title">Title *</Label>
              <Input
                id="title"
                placeholder="Enter task title"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                disabled={createTaskMutation.isPending}
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Enter task description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                disabled={createTaskMutation.isPending}
                rows={3}
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="project">Project</Label>
              <Select
                value={formData.project_id || 'no-project'}
                onValueChange={(value) =>
                  setFormData({
                    ...formData,
                    project_id: value === 'no-project' ? undefined : value,
                  })
                }
                disabled={createTaskMutation.isPending || loadingProjects}
              >
                <SelectTrigger id="project">
                  <SelectValue placeholder="Select a project (optional)">
                    {formData.project_id && (
                      <div className="flex items-center gap-2">
                        <div
                          className="h-3 w-3 rounded-full"
                          style={{
                            backgroundColor:
                              projects.find((p) => p.id === formData.project_id)?.color ||
                              '#6366f1',
                          }}
                        />
                        {projects.find((p) => p.id === formData.project_id)?.name}
                      </div>
                    )}
                  </SelectValue>
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="no-project">
                    <div className="flex items-center gap-2">
                      <FolderOpen className="h-4 w-4 text-muted-foreground" />
                      No Project
                    </div>
                  </SelectItem>
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

            <div className="grid gap-2">
              <Label>Categories</Label>
              <Popover open={categoriesOpen} onOpenChange={setCategoriesOpen}>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className="w-full justify-start text-left font-normal"
                    disabled={createTaskMutation.isPending}
                  >
                    {selectedCategories.length > 0 ? (
                      <div className="flex items-center gap-1 flex-wrap">
                        {selectedCategories.slice(0, 2).map((categoryId) => {
                          const category = categories.find((c) => c.id === categoryId);
                          if (!category) return null;
                          return (
                            <Badge
                              key={categoryId}
                              variant="secondary"
                              className="mr-1"
                              style={{
                                backgroundColor:
                                  CategoriesService.formatCategoryColor(category.color) + '20',
                                color: CategoriesService.formatCategoryColor(category.color),
                              }}
                            >
                              {CategoriesService.formatCategoryIcon(category.icon)} {category.name}
                            </Badge>
                          );
                        })}
                        {selectedCategories.length > 2 && (
                          <span className="text-muted-foreground text-sm">
                            +{selectedCategories.length - 2} more
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-muted-foreground">Select categories</span>
                    )}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-full p-0" align="start">
                  <div className="p-2 border-b">
                    <p className="text-sm font-medium">Select Categories</p>
                  </div>
                  <ScrollArea className="h-[200px]">
                    {categories.map((category) => (
                      <div
                        key={category.id}
                        className="flex items-center space-x-2 px-2 py-1.5 hover:bg-accent"
                      >
                        <Checkbox
                          id={`category-${category.id}`}
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
                        />
                        <label
                          htmlFor={`category-${category.id}`}
                          className="flex items-center gap-2 flex-1 cursor-pointer"
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
                          <span className="text-sm">{category.name}</span>
                        </label>
                      </div>
                    ))}
                  </ScrollArea>
                </PopoverContent>
              </Popover>
            </div>

            <div className="grid gap-2">
              <Label>Tags</Label>
              <Popover open={tagsOpen} onOpenChange={setTagsOpen}>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className="w-full justify-start text-left font-normal"
                    disabled={createTaskMutation.isPending}
                  >
                    {selectedTags.length > 0 ? (
                      <div className="flex items-center gap-1 flex-wrap">
                        {selectedTags.slice(0, 3).map((tagId) => {
                          const tag = tags.find((t) => t.id === tagId);
                          if (!tag) return null;
                          return (
                            <Badge
                              key={tagId}
                              variant="secondary"
                              className="mr-1"
                              style={{
                                backgroundColor: TagsService.formatTagColor(tag.color) + '20',
                                color: TagsService.formatTagColor(tag.color),
                              }}
                            >
                              <Hash className="h-3 w-3 mr-1" />
                              {tag.name}
                            </Badge>
                          );
                        })}
                        {selectedTags.length > 3 && (
                          <span className="text-muted-foreground text-sm">
                            +{selectedTags.length - 3} more
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-muted-foreground">Select tags</span>
                    )}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-full p-0" align="start">
                  <div className="p-2 border-b">
                    <p className="text-sm font-medium">Select Tags</p>
                  </div>
                  <ScrollArea className="h-[200px]">
                    {tags.map((tag) => (
                      <div
                        key={tag.id}
                        className="flex items-center space-x-2 px-2 py-1.5 hover:bg-accent"
                      >
                        <Checkbox
                          id={`tag-${tag.id}`}
                          checked={selectedTags.includes(tag.id)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setSelectedTags([...selectedTags, tag.id]);
                            } else {
                              setSelectedTags(selectedTags.filter((id) => id !== tag.id));
                            }
                          }}
                        />
                        <label
                          htmlFor={`tag-${tag.id}`}
                          className="flex items-center gap-2 flex-1 cursor-pointer"
                        >
                          <Badge
                            variant="outline"
                            className="text-xs"
                            style={{
                              backgroundColor: TagsService.formatTagColor(tag.color) + '20',
                              color: TagsService.formatTagColor(tag.color),
                              borderColor: TagsService.formatTagColor(tag.color),
                            }}
                          >
                            <Hash className="h-3 w-3 mr-1" />
                            {tag.name}
                          </Badge>
                        </label>
                      </div>
                    ))}
                  </ScrollArea>
                </PopoverContent>
              </Popover>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="status">Status</Label>
                <Select
                  value={formData.status}
                  onValueChange={(value) => setFormData({ ...formData, status: value as any })}
                  disabled={createTaskMutation.isPending}
                >
                  <SelectTrigger id="status">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="todo">To Do</SelectItem>
                    <SelectItem value="in_progress">In Progress</SelectItem>
                    <SelectItem value="done">Done</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="priority">Priority</Label>
                <Select
                  value={formData.priority}
                  onValueChange={(value) => setFormData({ ...formData, priority: value as any })}
                  disabled={createTaskMutation.isPending}
                >
                  <SelectTrigger id="priority">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="urgent">Urgent</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="start_date">Start Date</Label>
                <Input
                  id="start_date"
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  disabled={createTaskMutation.isPending}
                  min={format(new Date(), 'yyyy-MM-dd')}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="due_date">Due Date</Label>
                <Input
                  id="due_date"
                  type="date"
                  value={formData.due_date}
                  onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                  disabled={createTaskMutation.isPending}
                  min={format(new Date(), 'yyyy-MM-dd')}
                />
              </div>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="estimated_hours">Estimated Hours</Label>
              <Input
                id="estimated_hours"
                type="number"
                placeholder="0"
                value={formData.estimated_hours || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    estimated_hours: e.target.value ? parseFloat(e.target.value) : undefined,
                  })
                }
                disabled={createTaskMutation.isPending}
                min="0"
                step="0.5"
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={createTaskMutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createTaskMutation.isPending}>
              {createTaskMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {createTaskMutation.isPending ? 'Creating...' : 'Create Task'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
