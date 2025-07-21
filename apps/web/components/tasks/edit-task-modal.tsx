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
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { AlertCircle, Loader2, Trash2, FolderOpen } from 'lucide-react';
import { Task, UpdateTaskRequest } from '@/lib/api/tasks';
import { useUpdateTaskMutation, useDeleteTaskMutation } from '@/hooks/use-tasks-query';
import { format, parseISO } from 'date-fns';
import { Project, ProjectsService } from '@/lib/api/projects';
import { Category, CategoriesService } from '@/lib/api/categories';
import { Tag, TagsService } from '@/lib/api/tags';
import { useCategoriesQuery } from '@/hooks/use-categories-query';
import { useTagsQuery } from '@/hooks/use-tags-query';
import { Badge } from '@/components/ui/badge';
import { Hash, Folder } from 'lucide-react';
import { Checkbox } from '@/components/ui/checkbox';
import { TaskReminders } from './task-reminders';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

interface EditTaskModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  task: Task | null;
  onTaskUpdated?: () => void;
}

export function EditTaskModal({ open, onOpenChange, task, onTaskUpdated }: EditTaskModalProps) {
  const router = useRouter();
  const updateTaskMutation = useUpdateTaskMutation();
  const deleteTaskMutation = useDeleteTaskMutation();
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
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

  const [formData, setFormData] = useState<UpdateTaskRequest>({
    title: '',
    description: '',
    status: 'todo',
    priority: 'medium',
    due_date: '',
    start_date: '',
    estimated_hours: undefined,
    project_id: undefined,
    category_ids: [],
    tag_ids: [],
  });

  // Fetch projects when modal opens
  useEffect(() => {
    if (open) {
      fetchProjects();
    }
  }, [open]);

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

  // Update form data when task changes
  useEffect(() => {
    if (task) {
      setFormData({
        title: task.title,
        description: task.description || '',
        status: task.status,
        priority: task.priority,
        due_date: task.due_date ? format(parseISO(task.due_date), 'yyyy-MM-dd') : '',
        start_date: task.start_date ? format(parseISO(task.start_date), 'yyyy-MM-dd') : '',
        estimated_hours: task.estimated_hours,
        project_id: task.project_id,
        category_ids: task.categories?.map((c) => c.id) || [],
        tag_ids: task.tags?.map((t) => t.id) || [],
      });

      // Update selected categories and tags
      setSelectedCategories(task.categories?.map((c) => c.id) || []);
      setSelectedTags(task.tags?.map((t) => t.id) || []);
    }
  }, [task]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!task) return;

    if (!formData.title?.trim()) {
      return;
    }

    // Prepare the data - convert empty strings to undefined
    const taskData: UpdateTaskRequest = {
      ...formData,
      description: formData.description || undefined,
      due_date: formData.due_date || undefined,
      start_date: formData.start_date || undefined,
      estimated_hours: formData.estimated_hours || undefined,
      category_ids: selectedCategories,
      tag_ids: selectedTags,
    };

    updateTaskMutation.mutate(
      { id: task.id, data: taskData },
      {
        onSuccess: () => {
          // Close modal
          onOpenChange(false);

          // Notify parent component (optional now since React Query handles updates)
          if (onTaskUpdated) {
            onTaskUpdated();
          }
        },
      }
    );
  };

  const handleCancel = () => {
    // Reset form data to original task data
    if (task) {
      setFormData({
        title: task.title,
        description: task.description || '',
        status: task.status,
        priority: task.priority,
        due_date: task.due_date ? format(parseISO(task.due_date), 'yyyy-MM-dd') : '',
        start_date: task.start_date ? format(parseISO(task.start_date), 'yyyy-MM-dd') : '',
        estimated_hours: task.estimated_hours,
      });
    }
    updateTaskMutation.reset();
    deleteTaskMutation.reset();
    onOpenChange(false);
  };

  const handleDelete = async () => {
    if (!task) return;

    deleteTaskMutation.mutate(task.id, {
      onSuccess: () => {
        // Close both dialogs
        setShowDeleteDialog(false);
        onOpenChange(false);

        // Notify parent component (optional now since React Query handles updates)
        if (onTaskUpdated) {
          onTaskUpdated();
        }
      },
      onError: () => {
        // Close delete dialog on error
        setShowDeleteDialog(false);
      },
    });
  };

  if (!task) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[525px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Edit Task</DialogTitle>
            <DialogDescription>Update the task details below.</DialogDescription>
          </DialogHeader>

          {(updateTaskMutation.error || deleteTaskMutation.error) && (
            <Alert variant="destructive" className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {updateTaskMutation.error instanceof Error
                  ? updateTaskMutation.error.message
                  : deleteTaskMutation.error instanceof Error
                    ? deleteTaskMutation.error.message
                    : 'An error occurred'}
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
                disabled={updateTaskMutation.isPending || deleteTaskMutation.isPending}
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
                disabled={updateTaskMutation.isPending || deleteTaskMutation.isPending}
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
                disabled={
                  updateTaskMutation.isPending || deleteTaskMutation.isPending || loadingProjects
                }
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
                    disabled={updateTaskMutation.isPending || deleteTaskMutation.isPending}
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
                    disabled={updateTaskMutation.isPending || deleteTaskMutation.isPending}
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
                  disabled={updateTaskMutation.isPending || deleteTaskMutation.isPending}
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
                  disabled={updateTaskMutation.isPending || deleteTaskMutation.isPending}
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
                  disabled={updateTaskMutation.isPending || deleteTaskMutation.isPending}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="due_date">Due Date</Label>
                <Input
                  id="due_date"
                  type="date"
                  value={formData.due_date}
                  onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                  disabled={updateTaskMutation.isPending || deleteTaskMutation.isPending}
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
                disabled={updateTaskMutation.isPending || deleteTaskMutation.isPending}
                min="0"
                step="0.5"
              />
            </div>
          </div>

          {/* Reminders Section */}
          <TaskReminders task={task} className="mt-6" />

          <DialogFooter className="flex sm:justify-between">
            <Button
              type="button"
              variant="destructive"
              onClick={() => setShowDeleteDialog(true)}
              disabled={updateTaskMutation.isPending || deleteTaskMutation.isPending}
              className="sm:order-first"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </Button>
            <div className="flex space-x-2">
              <Button
                type="button"
                variant="outline"
                onClick={handleCancel}
                disabled={updateTaskMutation.isPending || deleteTaskMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={updateTaskMutation.isPending || deleteTaskMutation.isPending}
              >
                {updateTaskMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {updateTaskMutation.isPending ? 'Updating...' : 'Update Task'}
              </Button>
            </div>
          </DialogFooter>
        </form>
      </DialogContent>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the task "{task.title}" and
              remove it from our servers.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteTaskMutation.isPending}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleteTaskMutation.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteTaskMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {deleteTaskMutation.isPending ? 'Deleting...' : 'Delete Task'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Dialog>
  );
}
