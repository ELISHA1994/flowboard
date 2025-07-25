'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
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
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Calendar,
  Clock,
  Flag,
  CheckCircle2,
  Circle,
  XCircle,
  MoreHorizontal,
  Edit2,
  Trash2,
  Share2,
  Copy,
  Link2,
  Paperclip,
  MessageSquare,
  History,
  FolderOpen,
  X,
  Hash,
  ChevronRight,
  Timer,
  CalendarClock,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Task, TaskStatus, TaskPriority, UpdateTaskRequest } from '@/lib/api/tasks';
import { CommentsService, Comment } from '@/lib/api/comments';
import { Project, ProjectsService } from '@/lib/api/projects';
import { Category, CategoriesService } from '@/lib/api/categories';
import { Tag, TagsService } from '@/lib/api/tags';
import { format, formatDistanceToNow } from 'date-fns';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/contexts/auth-context';
import { TaskAttachments } from './task-attachments';
import { TaskActivity } from './task-activity';
import { TimeTracking } from './time-tracking';
import { Subtasks } from './subtasks';
import { TaskDependencies } from './task-dependencies';
import { TaskReminders } from './task-reminders';
import {
  useTaskQuery,
  useUpdateTaskMutation,
  useDeleteTaskMutation,
} from '@/hooks/use-tasks-query';
import { useCategoriesQuery } from '@/hooks/use-categories-query';
import { useTagsQuery } from '@/hooks/use-tags-query';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Checkbox } from '@/components/ui/checkbox';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface TaskDetailModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  taskId: string | null;
  onTaskUpdated?: () => void;
  onNavigateToTask?: (taskId: string) => void;
}

export function TaskDetailModal({
  open,
  onOpenChange,
  taskId,
  onTaskUpdated,
  onNavigateToTask,
}: TaskDetailModalProps) {
  const router = useRouter();
  const { toast } = useToast();
  const { user } = useAuth();

  const [comments, setComments] = useState<Comment[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [editedTask, setEditedTask] = useState<Partial<Task>>({});
  const [newComment, setNewComment] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [categoriesOpen, setCategoriesOpen] = useState(false);
  const [tagsOpen, setTagsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('subtasks');

  // Fetch task data
  const {
    data: task,
    isLoading: loading,
    error,
  } = useTaskQuery(taskId || '', {
    enabled: !!taskId && open,
  });
  const updateTaskMutation = useUpdateTaskMutation();
  const deleteTaskMutation = useDeleteTaskMutation();

  // Fetch categories and tags
  const { data: categories = [] } = useCategoriesQuery();
  const { data: tags = [] } = useTagsQuery();

  // Update editedTask when task data changes
  useEffect(() => {
    if (task) {
      setEditedTask(task);
      setSelectedCategories(task.categories?.map((c) => c.id) || []);
      setSelectedTags(task.tags?.map((t) => t.id) || []);
    }
  }, [task]);

  // Fetch projects when editing
  useEffect(() => {
    if (isEditing && projects.length === 0) {
      fetchProjects();
    }
  }, [isEditing]);

  // Fetch comments when task changes
  useEffect(() => {
    if (taskId && open) {
      fetchComments();
    }
  }, [taskId, open]);

  // Reset state when modal closes
  useEffect(() => {
    if (!open) {
      setIsEditing(false);
      setNewComment('');
      setActiveTab('subtasks');
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

  const fetchComments = async () => {
    if (!taskId) return;
    try {
      const fetchedComments = await CommentsService.getTaskComments(taskId);
      setComments(fetchedComments);
    } catch (error) {
      console.error('Failed to fetch comments:', error);
    }
  };

  const handleSaveTask = async () => {
    if (!task || !taskId) return;

    // Convert tag IDs to tag names for the backend
    const tagNames = selectedTags
      .map((tagId) => {
        const tag = tags.find((t) => t.id === tagId);
        return tag ? tag.name : '';
      })
      .filter((name) => name !== '');

    const updateData: UpdateTaskRequest = {
      title: editedTask.title || task.title,
      description: editedTask.description || task.description,
      status: editedTask.status || task.status,
      priority: editedTask.priority || task.priority,
      due_date: editedTask.due_date ?? task.due_date ?? undefined,
      start_date: editedTask.start_date ?? task.start_date ?? undefined,
      estimated_hours: editedTask.estimated_hours ?? task.estimated_hours ?? undefined,
      project_id:
        'project_id' in editedTask
          ? (editedTask.project_id ?? undefined)
          : (task.project_id ?? undefined),
      category_ids: selectedCategories,
      tag_names: tagNames,
    };

    updateTaskMutation.mutate(
      { id: taskId, data: updateData },
      {
        onSuccess: () => {
          setIsEditing(false);
          onTaskUpdated?.();
        },
      }
    );
  };

  const handleSubmitComment = async () => {
    if (!newComment.trim() || !taskId) return;

    try {
      setSubmittingComment(true);
      const comment = await CommentsService.createComment(taskId, {
        content: newComment,
      });
      setComments([...comments, comment]);
      setNewComment('');
      toast({
        title: 'Success',
        description: 'Comment added successfully',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to add comment',
        variant: 'destructive',
      });
    } finally {
      setSubmittingComment(false);
    }
  };

  const handleDelete = () => {
    if (!taskId) return;

    deleteTaskMutation.mutate(taskId, {
      onSuccess: () => {
        onOpenChange(false);
        onTaskUpdated?.();
      },
    });
  };

  // Keyboard shortcuts
  useEffect(() => {
    if (!open || !taskId) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + E to edit
      if ((e.metaKey || e.ctrlKey) && e.key === 'e') {
        e.preventDefault();
        if (!isEditing) {
          setIsEditing(true);
          fetchProjects();
        }
      }
      // Cmd/Ctrl + S to save (when editing)
      if ((e.metaKey || e.ctrlKey) && e.key === 's' && isEditing) {
        e.preventDefault();
        handleSaveTask();
      }
      // Cmd/Ctrl + D to delete
      if ((e.metaKey || e.ctrlKey) && e.key === 'd') {
        e.preventDefault();
        if (window.confirm('Are you sure you want to delete this task?')) {
          handleDelete();
        }
      }
      // Tab between tabs
      if (e.key === 'Tab' && !e.shiftKey && !isEditing) {
        e.preventDefault();
        const tabs = ['subtasks', 'comments', 'attachments', 'activity'];
        const currentIndex = tabs.indexOf(activeTab);
        const nextIndex = (currentIndex + 1) % tabs.length;
        setActiveTab(tabs[nextIndex]);
      }
      // Shift+Tab to go backwards
      if (e.key === 'Tab' && e.shiftKey && !isEditing) {
        e.preventDefault();
        const tabs = ['subtasks', 'comments', 'attachments', 'activity'];
        const currentIndex = tabs.indexOf(activeTab);
        const prevIndex = currentIndex === 0 ? tabs.length - 1 : currentIndex - 1;
        setActiveTab(tabs[prevIndex]);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, taskId, isEditing, activeTab]);

  const getStatusIcon = (status: TaskStatus) => {
    switch (status) {
      case 'done':
        return <CheckCircle2 className="h-5 w-5 text-green-600" />;
      case 'in_progress':
        return <Clock className="h-5 w-5 text-blue-600" />;
      case 'cancelled':
        return <XCircle className="h-5 w-5 text-gray-400" />;
      default:
        return <Circle className="h-5 w-5 text-gray-400" />;
    }
  };

  const getPriorityColor = (priority: TaskPriority) => {
    const colors: Record<TaskPriority, string> = {
      urgent: 'text-red-600',
      high: 'text-orange-600',
      medium: 'text-yellow-600',
      low: 'text-green-600',
    };
    return colors[priority];
  };

  if (!taskId || !open) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[calc(100vw-60px)] max-w-[calc(100vw-60px)] h-[calc(100vh-60px)] p-0 gap-0 sm:rounded-xl overflow-hidden">
        {/* Hidden dialog title for accessibility */}
        <DialogHeader className="sr-only">
          <DialogTitle>Task Details</DialogTitle>
          <DialogDescription>View and edit task information</DialogDescription>
        </DialogHeader>
        {loading ? (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
              <p className="mt-2 text-sm text-muted-foreground">Loading task...</p>
            </div>
          </div>
        ) : task ? (
          <div className="flex h-full">
            {/* Main Content Area */}
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Header */}
              <div className="bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-10 py-8 border-b">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    {isEditing ? (
                      <Input
                        value={editedTask.title}
                        onChange={(e) => setEditedTask({ ...editedTask, title: e.target.value })}
                        className="text-3xl font-semibold mb-4 h-auto py-2 border-0 px-0 focus-visible:ring-0"
                        placeholder="Task title"
                      />
                    ) : (
                      <h2 className="text-3xl font-semibold mb-4 truncate">{task.title}</h2>
                    )}
                    <div className="flex items-center gap-4 flex-wrap">
                      {/* Status */}
                      <div className="flex items-center gap-1.5">
                        {getStatusIcon(task.status)}
                        {isEditing ? (
                          <Select
                            value={editedTask.status}
                            onValueChange={(value) =>
                              setEditedTask({ ...editedTask, status: value as TaskStatus })
                            }
                          >
                            <SelectTrigger className="h-8 w-[140px]">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="todo">To Do</SelectItem>
                              <SelectItem value="in_progress">In Progress</SelectItem>
                              <SelectItem value="done">Done</SelectItem>
                              <SelectItem value="cancelled">Cancelled</SelectItem>
                            </SelectContent>
                          </Select>
                        ) : (
                          <span className="text-base font-medium capitalize">
                            {task.status.replace('_', ' ')}
                          </span>
                        )}
                      </div>

                      {/* Priority */}
                      <div className="flex items-center gap-1.5">
                        <Flag className={cn('h-4 w-4', getPriorityColor(task.priority))} />
                        {isEditing ? (
                          <Select
                            value={editedTask.priority}
                            onValueChange={(value) =>
                              setEditedTask({ ...editedTask, priority: value as TaskPriority })
                            }
                          >
                            <SelectTrigger className="h-8 w-[120px]">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="urgent">Urgent</SelectItem>
                              <SelectItem value="high">High</SelectItem>
                              <SelectItem value="medium">Medium</SelectItem>
                              <SelectItem value="low">Low</SelectItem>
                            </SelectContent>
                          </Select>
                        ) : (
                          <span
                            className={cn(
                              'text-base font-medium capitalize',
                              getPriorityColor(task.priority)
                            )}
                          >
                            {task.priority}
                          </span>
                        )}
                      </div>

                      {/* Project */}
                      {task.project && !isEditing && (
                        <div className="flex items-center gap-1.5">
                          <div
                            className="h-3 w-3 rounded-full"
                            style={{ backgroundColor: task.project.color || '#6366f1' }}
                          />
                          <span className="text-sm">{task.project.name}</span>
                        </div>
                      )}

                      {/* Tags */}
                      {task.tags.length > 0 && !isEditing && (
                        <div className="flex items-center gap-1.5">
                          {task.tags.slice(0, 3).map((tag) => (
                            <Badge
                              key={tag.id}
                              variant="outline"
                              className="text-xs h-6"
                              style={{
                                backgroundColor: TagsService.formatTagColor(tag.color) + '20',
                                color: TagsService.formatTagColor(tag.color),
                                borderColor: TagsService.formatTagColor(tag.color),
                              }}
                            >
                              <Hash className="h-3 w-3 mr-1" />
                              {tag.name}
                            </Badge>
                          ))}
                          {task.tags.length > 3 && (
                            <span className="text-xs text-muted-foreground">
                              +{task.tags.length - 3} more
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {isEditing ? (
                      <>
                        <Button variant="ghost" size="sm" onClick={() => setIsEditing(false)}>
                          Cancel
                        </Button>
                        <Button size="sm" onClick={handleSaveTask}>
                          Save
                        </Button>
                      </>
                    ) : (
                      <>
                        <TooltipProvider>
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button variant="ghost" size="sm" onClick={() => setIsEditing(true)}>
                                <Edit2 className="h-4 w-4" />
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent>
                              <p>Edit task</p>
                              <p className="text-xs text-muted-foreground">⌘E</p>
                            </TooltipContent>
                          </Tooltip>
                        </TooltipProvider>
                        <Button variant="ghost" size="sm">
                          <Share2 className="h-4 w-4" />
                        </Button>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>
                              <Copy className="mr-2 h-4 w-4" />
                              Duplicate
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Link2 className="mr-2 h-4 w-4" />
                              Copy link
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="text-destructive" onClick={handleDelete}>
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onOpenChange(false)}
                          className="ml-2"
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Content Area with Tabs */}
              <div className="flex-1 overflow-hidden flex flex-col">
                <ScrollArea className="flex-1">
                  <div className="p-8">
                    {/* Description */}
                    <div className="mb-8">
                      <h3 className="text-base font-medium mb-3">Description</h3>
                      {isEditing ? (
                        <Textarea
                          value={editedTask.description || ''}
                          onChange={(e) =>
                            setEditedTask({ ...editedTask, description: e.target.value })
                          }
                          placeholder="Add a description..."
                          className="min-h-[120px] text-base"
                        />
                      ) : (
                        <p className="whitespace-pre-wrap text-base leading-relaxed">
                          {task.description || (
                            <span className="text-muted-foreground">No description</span>
                          )}
                        </p>
                      )}
                    </div>

                    {/* User Story Section (if description contains user story) */}
                    {task.description && task.description.includes('User Story:') && (
                      <div className="mb-6 p-4 bg-muted/50 rounded-lg">
                        <h3 className="text-sm font-medium mb-2">User Story</h3>
                        <p className="text-sm whitespace-pre-wrap">
                          {task.description.split('User Story:')[1]?.split('\n\n')[0] || ''}
                        </p>
                      </div>
                    )}

                    {/* Tabs */}
                    <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full mt-6">
                      <TabsList className="grid w-full grid-cols-4 h-12">
                        <TabsTrigger value="subtasks">Subtasks</TabsTrigger>
                        <TabsTrigger value="comments">
                          <MessageSquare className="mr-2 h-4 w-4" />
                          Comments ({comments.length})
                        </TabsTrigger>
                        <TabsTrigger value="attachments">
                          <Paperclip className="mr-2 h-4 w-4" />
                          Attachments
                        </TabsTrigger>
                        <TabsTrigger value="activity">
                          <History className="mr-2 h-4 w-4" />
                          Activity
                        </TabsTrigger>
                      </TabsList>

                      <TabsContent value="subtasks" className="mt-4">
                        <Subtasks parentTask={task} />
                      </TabsContent>

                      <TabsContent value="comments" className="mt-4">
                        {/* Comment Input */}
                        <div className="mb-6">
                          <div className="flex gap-3">
                            <Avatar className="h-8 w-8">
                              <AvatarFallback>
                                {user?.username?.slice(0, 2).toUpperCase() || 'U'}
                              </AvatarFallback>
                            </Avatar>
                            <div className="flex-1">
                              <Textarea
                                placeholder="Add a comment..."
                                value={newComment}
                                onChange={(e) => setNewComment(e.target.value)}
                                className="min-h-[80px]"
                              />
                              <div className="mt-2 flex justify-end">
                                <Button
                                  size="sm"
                                  onClick={handleSubmitComment}
                                  disabled={!newComment.trim() || submittingComment}
                                >
                                  {submittingComment ? 'Posting...' : 'Post comment'}
                                </Button>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Comments List */}
                        <div className="space-y-4">
                          {comments.length === 0 ? (
                            <p className="text-center text-sm text-muted-foreground">
                              No comments yet. Be the first to comment!
                            </p>
                          ) : (
                            comments.map((comment) => (
                              <div key={comment.id} className="flex gap-3">
                                <Avatar className="h-8 w-8">
                                  <AvatarFallback>
                                    {comment.user.username.slice(0, 2).toUpperCase()}
                                  </AvatarFallback>
                                </Avatar>
                                <div className="flex-1">
                                  <div className="flex items-center gap-2">
                                    <span className="font-medium text-sm">
                                      {comment.user.username}
                                    </span>
                                    <span className="text-xs text-muted-foreground">
                                      {formatDistanceToNow(new Date(comment.created_at), {
                                        addSuffix: true,
                                      })}
                                    </span>
                                  </div>
                                  <p className="mt-1 text-sm whitespace-pre-wrap">
                                    {comment.content}
                                  </p>
                                </div>
                              </div>
                            ))
                          )}
                        </div>
                      </TabsContent>

                      <TabsContent value="attachments" className="mt-4">
                        <TaskAttachments taskId={taskId} canEdit={true} />
                      </TabsContent>

                      <TabsContent value="activity" className="mt-4">
                        <TaskActivity taskId={taskId} task={task} />
                      </TabsContent>
                    </Tabs>
                  </div>
                </ScrollArea>
              </div>
            </div>

            {/* Right Sidebar */}
            <div className="w-[400px] border-l bg-muted/20 flex flex-col">
              <ScrollArea className="flex-1">
                <div className="p-6 space-y-8">
                  {/* Properties */}
                  <div>
                    <h3 className="text-sm font-medium mb-3">Properties</h3>
                    <div className="space-y-4">
                      {/* Assignee */}
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Assignee</p>
                        {task.assigned_to ? (
                          <div className="flex items-center gap-2">
                            <Avatar className="h-6 w-6">
                              <AvatarFallback className="text-xs">
                                {task.assigned_to.username.slice(0, 2).toUpperCase()}
                              </AvatarFallback>
                            </Avatar>
                            <span className="text-sm">{task.assigned_to.username}</span>
                          </div>
                        ) : (
                          <p className="text-sm text-muted-foreground">Unassigned</p>
                        )}
                      </div>

                      {/* Dates */}
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">Start Date</p>
                          {isEditing ? (
                            <Input
                              type="date"
                              value={
                                editedTask.start_date ? editedTask.start_date.slice(0, 10) : ''
                              }
                              onChange={(e) =>
                                setEditedTask({
                                  ...editedTask,
                                  start_date: e.target.value
                                    ? new Date(e.target.value).toISOString()
                                    : null,
                                })
                              }
                              className="h-8"
                            />
                          ) : (
                            <div className="flex items-center gap-1.5 text-sm">
                              <CalendarClock className="h-3 w-3 text-muted-foreground" />
                              {task.start_date ? (
                                format(new Date(task.start_date), 'MMM d')
                              ) : (
                                <span className="text-muted-foreground">Not set</span>
                              )}
                            </div>
                          )}
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">Due Date</p>
                          {isEditing ? (
                            <Input
                              type="date"
                              value={editedTask.due_date ? editedTask.due_date.slice(0, 10) : ''}
                              onChange={(e) =>
                                setEditedTask({
                                  ...editedTask,
                                  due_date: e.target.value
                                    ? new Date(e.target.value).toISOString()
                                    : null,
                                })
                              }
                              className="h-8"
                            />
                          ) : (
                            <div className="flex items-center gap-1.5 text-sm">
                              <Calendar className="h-3 w-3 text-muted-foreground" />
                              {task.due_date ? (
                                format(new Date(task.due_date), 'MMM d')
                              ) : (
                                <span className="text-muted-foreground">Not set</span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Time Estimates */}
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">Estimated</p>
                          {isEditing ? (
                            <Input
                              type="number"
                              value={editedTask.estimated_hours || ''}
                              onChange={(e) =>
                                setEditedTask({
                                  ...editedTask,
                                  estimated_hours: e.target.value
                                    ? parseFloat(e.target.value)
                                    : null,
                                })
                              }
                              step="0.5"
                              min="0"
                              className="h-8"
                              placeholder="0"
                            />
                          ) : (
                            <div className="flex items-center gap-1.5 text-sm">
                              <Timer className="h-3 w-3 text-muted-foreground" />
                              {task.estimated_hours ? (
                                `${task.estimated_hours}h`
                              ) : (
                                <span className="text-muted-foreground">Not set</span>
                              )}
                            </div>
                          )}
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">Actual</p>
                          <div className="flex items-center gap-1.5 text-sm">
                            <Clock className="h-3 w-3 text-muted-foreground" />
                            {task.actual_hours || 0}h
                          </div>
                        </div>
                      </div>

                      {/* Project */}
                      {isEditing && (
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">Project</p>
                          <Select
                            value={editedTask.project_id || 'no-project'}
                            onValueChange={(value) =>
                              setEditedTask({
                                ...editedTask,
                                project_id: value === 'no-project' ? undefined : value,
                              })
                            }
                            disabled={loadingProjects}
                          >
                            <SelectTrigger className="h-8">
                              <SelectValue placeholder="Select a project">
                                {editedTask.project_id && (
                                  <div className="flex items-center gap-2">
                                    <div
                                      className="h-3 w-3 rounded-full"
                                      style={{
                                        backgroundColor:
                                          projects.find((p) => p.id === editedTask.project_id)
                                            ?.color || '#6366f1',
                                      }}
                                    />
                                    {projects.find((p) => p.id === editedTask.project_id)?.name}
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
                      )}

                      {/* Categories */}
                      {isEditing && (
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">Categories</p>
                          <Popover open={categoriesOpen} onOpenChange={setCategoriesOpen}>
                            <PopoverTrigger asChild>
                              <Button
                                variant="outline"
                                className="w-full justify-start text-left font-normal h-8"
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
                                          className="text-xs"
                                          style={{
                                            backgroundColor:
                                              CategoriesService.formatCategoryColor(
                                                category.color
                                              ) + '20',
                                            color: CategoriesService.formatCategoryColor(
                                              category.color
                                            ),
                                          }}
                                        >
                                          {CategoriesService.formatCategoryIcon(category.icon)}{' '}
                                          {category.name}
                                        </Badge>
                                      );
                                    })}
                                    {selectedCategories.length > 2 && (
                                      <span className="text-xs text-muted-foreground">
                                        +{selectedCategories.length - 2}
                                      </span>
                                    )}
                                  </div>
                                ) : (
                                  <span className="text-muted-foreground text-sm">
                                    Select categories
                                  </span>
                                )}
                              </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-64 p-0" align="start">
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
                                          setSelectedCategories([
                                            ...selectedCategories,
                                            category.id,
                                          ]);
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
                                        className="h-5 w-5 rounded flex items-center justify-center text-xs"
                                        style={{
                                          backgroundColor:
                                            CategoriesService.formatCategoryColor(category.color) +
                                            '20',
                                          color: CategoriesService.formatCategoryColor(
                                            category.color
                                          ),
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
                      )}

                      {/* Tags */}
                      {isEditing && (
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">Tags</p>
                          <Popover open={tagsOpen} onOpenChange={setTagsOpen}>
                            <PopoverTrigger asChild>
                              <Button
                                variant="outline"
                                className="w-full justify-start text-left font-normal h-8"
                              >
                                {selectedTags.length > 0 ? (
                                  <div className="flex items-center gap-1 flex-wrap">
                                    {selectedTags.slice(0, 2).map((tagId) => {
                                      const tag = tags.find((t) => t.id === tagId);
                                      if (!tag) return null;
                                      return (
                                        <Badge
                                          key={tagId}
                                          variant="outline"
                                          className="text-xs"
                                          style={{
                                            backgroundColor:
                                              TagsService.formatTagColor(tag.color) + '20',
                                            color: TagsService.formatTagColor(tag.color),
                                            borderColor: TagsService.formatTagColor(tag.color),
                                          }}
                                        >
                                          <Hash className="h-3 w-3 mr-1" />
                                          {tag.name}
                                        </Badge>
                                      );
                                    })}
                                    {selectedTags.length > 2 && (
                                      <span className="text-xs text-muted-foreground">
                                        +{selectedTags.length - 2}
                                      </span>
                                    )}
                                  </div>
                                ) : (
                                  <span className="text-muted-foreground text-sm">Select tags</span>
                                )}
                              </Button>
                            </PopoverTrigger>
                            <PopoverContent className="w-64 p-0" align="start">
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
                                          setSelectedTags(
                                            selectedTags.filter((id) => id !== tag.id)
                                          );
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
                                          backgroundColor:
                                            TagsService.formatTagColor(tag.color) + '20',
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
                      )}

                      {!isEditing && (
                        <>
                          {/* Categories Display */}
                          {task.categories.length > 0 && (
                            <div>
                              <p className="text-xs text-muted-foreground mb-1">Categories</p>
                              <div className="flex flex-wrap gap-1">
                                {task.categories.map((category) => (
                                  <Badge
                                    key={category.id}
                                    variant="secondary"
                                    className="text-xs"
                                    style={{
                                      backgroundColor:
                                        CategoriesService.formatCategoryColor(category.color) +
                                        '20',
                                      color: CategoriesService.formatCategoryColor(category.color),
                                    }}
                                  >
                                    {CategoriesService.formatCategoryIcon(category.icon)}{' '}
                                    {category.name}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </div>

                  <Separator />

                  {/* Time Tracking */}
                  <div>
                    <h3 className="text-sm font-medium mb-3">Time Tracking</h3>
                    <TimeTracking task={task} onTimeLogged={fetchComments} />
                  </div>

                  <Separator />

                  {/* Reminders */}
                  <div>
                    <h3 className="text-sm font-medium mb-3">Reminders</h3>
                    <TaskReminders task={task} />
                  </div>

                  {/* Dependencies */}
                  {task.dependencies.length > 0 && (
                    <>
                      <Separator />
                      <div>
                        <h3 className="text-sm font-medium mb-3">Dependencies</h3>
                        <div className="space-y-1">
                          {task.dependencies.map((dep) => (
                            <div key={dep.id} className="text-sm">
                              <Link2 className="mr-1.5 inline h-3 w-3" />
                              {dep.depends_on.title}
                            </div>
                          ))}
                        </div>
                      </div>
                    </>
                  )}

                  {/* Activity Summary */}
                  <div className="mt-auto pt-4 border-t">
                    <div className="text-xs text-muted-foreground space-y-1">
                      <p>Created {format(new Date(task.created_at), 'MMM d, yyyy')}</p>
                      {task.updated_at && (
                        <p>
                          Updated{' '}
                          {formatDistanceToNow(new Date(task.updated_at), { addSuffix: true })}
                        </p>
                      )}
                    </div>
                    <div className="mt-3 pt-3 border-t">
                      <p className="text-xs text-muted-foreground font-medium mb-1">
                        Keyboard shortcuts
                      </p>
                      <div className="text-xs text-muted-foreground space-y-0.5">
                        <p>⌘E - Edit task</p>
                        <p>⌘S - Save changes</p>
                        <p>Tab - Navigate tabs</p>
                      </div>
                    </div>
                  </div>
                </div>
              </ScrollArea>
            </div>
          </div>
        ) : (
          <div className="flex h-full items-center justify-center">
            <p className="text-sm text-muted-foreground">Task not found</p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
