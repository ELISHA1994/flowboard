'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { DashboardLayout } from '@/components/layouts/dashboard-layout';
import { Breadcrumb } from '@/components/ui/breadcrumb';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
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
} from '@/components/ui/dropdown-menu';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
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
  CalendarClock,
  Timer,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { TasksService, Task, TaskStatus, TaskPriority } from '@/lib/api/tasks';
import { CommentsService, Comment } from '@/lib/api/comments';
import { format, formatDistanceToNow } from 'date-fns';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/contexts/auth-context';
import { TaskAttachments } from '@/components/tasks/task-attachments';
import { TaskActivity } from '@/components/tasks/task-activity';
import { TimeTracking } from '@/components/tasks/time-tracking';
import { Subtasks } from '@/components/tasks/subtasks';
import { TaskDependencies } from '@/components/tasks/task-dependencies';

export default function TaskDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const { user } = useAuth();
  const taskId = params.taskId as string;

  const [task, setTask] = useState<Task | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editedTask, setEditedTask] = useState<Partial<Task>>({});
  const [newComment, setNewComment] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);

  // Fetch task details
  const fetchTask = async () => {
    try {
      setLoading(true);
      const fetchedTask = await TasksService.getTask(taskId);
      setTask(fetchedTask);
      setEditedTask(fetchedTask);
    } catch (error) {
      console.error('Failed to fetch task:', error);
      toast({
        title: 'Error',
        description: 'Failed to load task details.',
        variant: 'destructive',
      });
      router.push('/tasks');
    } finally {
      setLoading(false);
    }
  };

  // Fetch comments
  const fetchComments = async () => {
    try {
      const fetchedComments = await CommentsService.getTaskComments(taskId);
      setComments(fetchedComments);
    } catch (error) {
      console.error('Failed to fetch comments:', error);
    }
  };

  useEffect(() => {
    fetchTask();
    fetchComments();
  }, [taskId]);

  // Handle task update
  const handleSaveTask = async () => {
    if (!task) return;

    try {
      const updatedTask = await TasksService.updateTask(taskId, {
        title: editedTask.title || task.title,
        description: editedTask.description || task.description,
        status: editedTask.status || task.status,
        priority: editedTask.priority || task.priority,
        due_date: editedTask.due_date || task.due_date,
        start_date: editedTask.start_date || task.start_date,
        estimated_hours: editedTask.estimated_hours || task.estimated_hours,
      });
      setTask(updatedTask);
      setIsEditing(false);
      toast({
        title: 'Success',
        description: 'Task updated successfully',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update task',
        variant: 'destructive',
      });
    }
  };

  // Handle comment submission
  const handleSubmitComment = async () => {
    if (!newComment.trim()) return;

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

  // Get status icon
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

  // Get priority color
  const getPriorityColor = (priority: TaskPriority) => {
    const colors: Record<TaskPriority, string> = {
      urgent: 'text-red-600',
      high: 'text-orange-600',
      medium: 'text-yellow-600',
      low: 'text-green-600',
    };
    return colors[priority];
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="mt-2 text-sm text-muted-foreground">Loading task...</p>
        </div>
      </div>
    );
  }

  if (!task) {
    return null;
  }

  const breadcrumbItems = [
    { label: 'Tasks', href: '/tasks' },
    { label: task.title, href: undefined },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Breadcrumb Navigation */}
        <div className="flex items-center justify-between">
          <Breadcrumb items={breadcrumbItems} />
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>ID:</span>
            <span className="font-mono">{task.id.slice(0, 8)}</span>
          </div>
        </div>

        {/* Action Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">{task.title}</h1>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <Share2 className="mr-2 h-4 w-4" />
              Share
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
                <DropdownMenuItem
                  className="text-destructive"
                  onClick={async () => {
                    try {
                      await TasksService.deleteTask(taskId);
                      toast({
                        title: 'Success',
                        description: 'Task deleted successfully',
                      });
                      router.push('/tasks');
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
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Task Details */}
        <div className="flex-1 overflow-auto">
          <div className="mx-auto max-w-4xl p-6">
            {/* Title and Status */}
            <div className="mb-6">
              <div className="mb-4 flex items-start justify-between">
                {isEditing ? (
                  <Input
                    value={editedTask.title}
                    onChange={(e) => setEditedTask({ ...editedTask, title: e.target.value })}
                    className="text-2xl font-semibold"
                    placeholder="Task title"
                  />
                ) : (
                  <h1 className="text-2xl font-semibold">{task.title}</h1>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    if (isEditing) {
                      handleSaveTask();
                    } else {
                      setIsEditing(true);
                    }
                  }}
                >
                  {isEditing ? 'Save' : <Edit2 className="h-4 w-4" />}
                </Button>
              </div>

              <div className="flex items-center gap-4">
                {/* Status */}
                <div className="flex items-center gap-2">
                  {getStatusIcon(task.status)}
                  {isEditing ? (
                    <Select
                      value={editedTask.status}
                      onValueChange={(value) =>
                        setEditedTask({ ...editedTask, status: value as TaskStatus })
                      }
                    >
                      <SelectTrigger className="w-[140px]">
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
                    <span className="font-medium">{task.status.replace('_', ' ')}</span>
                  )}
                </div>

                {/* Priority */}
                <div className="flex items-center gap-2">
                  <Flag className={cn('h-4 w-4', getPriorityColor(task.priority))} />
                  {isEditing ? (
                    <Select
                      value={editedTask.priority}
                      onValueChange={(value) =>
                        setEditedTask({ ...editedTask, priority: value as TaskPriority })
                      }
                    >
                      <SelectTrigger className="w-[120px]">
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
                    <span className={cn('font-medium', getPriorityColor(task.priority))}>
                      {task.priority}
                    </span>
                  )}
                </div>

                {/* Tags */}
                {task.tags.length > 0 && (
                  <div className="flex items-center gap-2">
                    {task.tags.map((tag) => (
                      <Badge key={tag.id} variant="outline">
                        {tag.name}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Description */}
            <div className="mb-8">
              <h3 className="mb-2 text-sm font-medium text-muted-foreground">Description</h3>
              {isEditing ? (
                <Textarea
                  value={editedTask.description || ''}
                  onChange={(e) => setEditedTask({ ...editedTask, description: e.target.value })}
                  placeholder="Add a description..."
                  className="min-h-[100px]"
                />
              ) : (
                <p className="whitespace-pre-wrap text-sm">
                  {task.description || (
                    <span className="text-muted-foreground">No description</span>
                  )}
                </p>
              )}
            </div>

            {/* Subtasks */}
            <div className="mb-8">
              <Subtasks parentTask={task} onUpdate={fetchTask} />
            </div>

            {/* Metadata */}
            <div className="mb-8 grid grid-cols-2 gap-6">
              <div>
                <h3 className="mb-2 text-sm font-medium text-muted-foreground">Due Date</h3>
                {isEditing ? (
                  <Input
                    type="datetime-local"
                    value={editedTask.due_date?.slice(0, 16) || ''}
                    onChange={(e) =>
                      setEditedTask({
                        ...editedTask,
                        due_date: e.target.value ? new Date(e.target.value).toISOString() : null,
                      })
                    }
                  />
                ) : (
                  <div className="flex items-center gap-2 text-sm">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    {task.due_date ? (
                      format(new Date(task.due_date), 'MMM d, yyyy h:mm a')
                    ) : (
                      <span className="text-muted-foreground">Not set</span>
                    )}
                  </div>
                )}
              </div>

              <div>
                <h3 className="mb-2 text-sm font-medium text-muted-foreground">Start Date</h3>
                {isEditing ? (
                  <Input
                    type="datetime-local"
                    value={editedTask.start_date?.slice(0, 16) || ''}
                    onChange={(e) =>
                      setEditedTask({
                        ...editedTask,
                        start_date: e.target.value ? new Date(e.target.value).toISOString() : null,
                      })
                    }
                  />
                ) : (
                  <div className="flex items-center gap-2 text-sm">
                    <CalendarClock className="h-4 w-4 text-muted-foreground" />
                    {task.start_date ? (
                      format(new Date(task.start_date), 'MMM d, yyyy h:mm a')
                    ) : (
                      <span className="text-muted-foreground">Not set</span>
                    )}
                  </div>
                )}
              </div>

              <div>
                <h3 className="mb-2 text-sm font-medium text-muted-foreground">Estimated Hours</h3>
                {isEditing ? (
                  <Input
                    type="number"
                    value={editedTask.estimated_hours || ''}
                    onChange={(e) =>
                      setEditedTask({
                        ...editedTask,
                        estimated_hours: e.target.value ? parseFloat(e.target.value) : null,
                      })
                    }
                    step="0.5"
                    min="0"
                  />
                ) : (
                  <div className="flex items-center gap-2 text-sm">
                    <Timer className="h-4 w-4 text-muted-foreground" />
                    {task.estimated_hours ? (
                      `${task.estimated_hours} hours`
                    ) : (
                      <span className="text-muted-foreground">Not set</span>
                    )}
                  </div>
                )}
              </div>

              <div>
                <h3 className="mb-2 text-sm font-medium text-muted-foreground">Actual Hours</h3>
                <div className="flex items-center gap-2 text-sm">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  {task.actual_hours || 0} hours
                </div>
              </div>

              <div>
                <h3 className="mb-2 text-sm font-medium text-muted-foreground">Created</h3>
                <p className="text-sm">{format(new Date(task.created_at), 'MMM d, yyyy h:mm a')}</p>
              </div>

              <div>
                <h3 className="mb-2 text-sm font-medium text-muted-foreground">Last Updated</h3>
                <p className="text-sm">
                  {task.updated_at && task.updated_at !== null
                    ? formatDistanceToNow(new Date(task.updated_at), { addSuffix: true })
                    : format(new Date(task.created_at), 'MMM d, yyyy h:mm a')}
                </p>
              </div>
            </div>

            {/* Tabs for Comments and Activity */}
            <Tabs defaultValue="comments" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="comments">
                  <MessageSquare className="mr-2 h-4 w-4" />
                  Comments
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

              <TabsContent value="comments" className="mt-6">
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
                            <span className="font-medium text-sm">{comment.user.username}</span>
                            <span className="text-xs text-muted-foreground">
                              {formatDistanceToNow(new Date(comment.created_at), {
                                addSuffix: true,
                              })}
                            </span>
                          </div>
                          <p className="mt-1 text-sm whitespace-pre-wrap">{comment.content}</p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </TabsContent>

              <TabsContent value="attachments" className="mt-6">
                <TaskAttachments taskId={taskId} canEdit={true} />
              </TabsContent>

              <TabsContent value="activity" className="mt-6">
                <TaskActivity taskId={taskId} task={task} />
              </TabsContent>
            </Tabs>
          </div>
        </div>

        {/* Sidebar */}
        <div className="w-80 border-l bg-muted/20 p-6">
          <h3 className="mb-4 text-sm font-medium">Properties</h3>
          <div className="space-y-4">
            <div>
              <p className="mb-1 text-xs text-muted-foreground">Assigned to</p>
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

            <div>
              <p className="mb-1 text-xs text-muted-foreground">Project</p>
              {task.project ? (
                <div className="flex items-center gap-2">
                  <FolderOpen className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">{task.project.name}</span>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No project</p>
              )}
            </div>

            <div>
              <p className="mb-1 text-xs text-muted-foreground">Categories</p>
              {task.categories.length > 0 ? (
                <div className="flex flex-wrap gap-1">
                  {task.categories.map((category) => (
                    <Badge key={category.id} variant="secondary" className="text-xs">
                      {category.name}
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No categories</p>
              )}
            </div>

            {task.dependencies.length > 0 && (
              <div>
                <p className="mb-1 text-xs text-muted-foreground">Dependencies</p>
                <div className="space-y-1">
                  {task.dependencies.map((dep) => (
                    <div key={dep.id} className="text-sm">
                      <Link2 className="mr-1 inline h-3 w-3" />
                      {dep.depends_on.title}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Time Tracking */}
          <Separator className="my-4" />
          <div>
            <h3 className="mb-4 text-sm font-medium">Time Tracking</h3>
            <TimeTracking task={task} onTimeLogged={fetchTask} />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
