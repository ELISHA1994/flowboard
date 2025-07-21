'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import {
  Plus,
  Target,
  CheckCircle2,
  Circle,
  Clock,
  XCircle,
  MoreHorizontal,
  Edit,
  Trash2,
  Loader2,
} from 'lucide-react';
import { Task } from '@/lib/api/tasks';
import { cn } from '@/lib/utils';
import {
  useSubtasksQuery,
  useCreateSubtaskMutation,
  useUpdateSubtaskMutation,
  useDeleteSubtaskMutation,
} from '@/hooks/use-subtasks-query';

interface SubtasksProps {
  parentTask: Task;
  onUpdate?: () => void; // Legacy prop for backward compatibility
}

export function Subtasks({ parentTask }: SubtasksProps) {
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newSubtaskTitle, setNewSubtaskTitle] = useState('');

  // Use advanced TanStack Query hooks
  const { data: subtasks = [], isLoading, isError, error } = useSubtasksQuery(parentTask.id);

  const createSubtaskMutation = useCreateSubtaskMutation(parentTask.id);
  const updateSubtaskMutation = useUpdateSubtaskMutation(parentTask.id);
  const deleteSubtaskMutation = useDeleteSubtaskMutation(parentTask.id);

  // Create subtask handler
  const handleCreateSubtask = async () => {
    if (!newSubtaskTitle.trim()) return;

    createSubtaskMutation.mutate(
      {
        title: newSubtaskTitle,
        status: 'todo',
        priority: 'medium',
        parent_task_id: parentTask.id,
      },
      {
        onSuccess: () => {
          setNewSubtaskTitle('');
          setShowCreateDialog(false);
        },
      }
    );
  };

  // Toggle subtask status handler with optimistic updates
  const handleToggleStatus = (subtask: Task) => {
    const newStatus = subtask.status === 'done' ? 'todo' : 'done';

    updateSubtaskMutation.mutate({
      id: subtask.id,
      data: { status: newStatus },
    });
  };

  // Delete subtask handler
  const handleDeleteSubtask = (subtaskId: string) => {
    deleteSubtaskMutation.mutate(subtaskId);
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
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

  const completedCount = subtasks.filter((st) => st.status === 'done').length;
  const totalCount = subtasks.length;
  const progress = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

  // Error state
  if (isError) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4 text-muted-foreground" />
            <h4 className="text-sm font-medium">Subtasks</h4>
          </div>
          <Button variant="outline" size="sm" onClick={() => setShowCreateDialog(true)}>
            <Plus className="mr-1 h-3 w-3" />
            Add
          </Button>
        </div>

        <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4 text-center">
          <p className="text-sm text-destructive">
            Failed to load subtasks: {error instanceof Error ? error.message : 'Unknown error'}
          </p>
        </div>
      </div>
    );
  }

  // Loading state with skeletons
  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4 text-muted-foreground" />
            <h4 className="text-sm font-medium">Subtasks</h4>
            <Skeleton className="h-5 w-12" />
          </div>
          <Button variant="outline" size="sm" disabled>
            <Plus className="mr-1 h-3 w-3" />
            Add
          </Button>
        </div>

        <div className="space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="flex items-center gap-3 rounded-lg border p-3">
              <Skeleton className="h-4 w-4" />
              <div className="flex-1">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="mt-1 h-3 w-1/2" />
              </div>
              <Skeleton className="h-4 w-4" />
              <Skeleton className="h-8 w-8" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Target className="h-4 w-4 text-muted-foreground" />
          <h4 className="text-sm font-medium">Subtasks</h4>
          {totalCount > 0 && (
            <Badge variant="secondary" className="text-xs">
              {completedCount}/{totalCount}
            </Badge>
          )}
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowCreateDialog(true)}
          disabled={createSubtaskMutation.isPending}
        >
          {createSubtaskMutation.isPending ? (
            <Loader2 className="mr-1 h-3 w-3 animate-spin" />
          ) : (
            <Plus className="mr-1 h-3 w-3" />
          )}
          Add
        </Button>
      </div>

      {/* Progress bar */}
      {totalCount > 0 && (
        <div className="space-y-1">
          <div className="h-2 bg-secondary rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-xs text-muted-foreground text-right">
            {Math.round(progress)}% complete
          </p>
        </div>
      )}

      {/* Optimistic loading for create mutation */}
      {createSubtaskMutation.isPending && (
        <div className="flex items-center gap-3 rounded-lg border p-3 bg-muted/20 animate-pulse">
          <Checkbox disabled />
          <div className="flex-1">
            <p className="text-sm opacity-60">{createSubtaskMutation.variables?.title}</p>
          </div>
          <Circle className="h-4 w-4 text-gray-400 opacity-60" />
          <Loader2 className="h-4 w-4 animate-spin opacity-60" />
        </div>
      )}

      {/* Subtasks list */}
      {subtasks.length === 0 && !createSubtaskMutation.isPending ? (
        <div className="rounded-lg border border-dashed p-4 text-center">
          <Target className="mx-auto h-8 w-8 text-muted-foreground/50" />
          <p className="mt-2 text-sm text-muted-foreground">No subtasks yet</p>
          <Button
            variant="link"
            size="sm"
            className="mt-1"
            onClick={() => setShowCreateDialog(true)}
          >
            Create first subtask
          </Button>
        </div>
      ) : (
        <div className="space-y-2">
          {subtasks.map((subtask) => {
            const isUpdating =
              updateSubtaskMutation.isPending && updateSubtaskMutation.variables?.id === subtask.id;
            const isDeleting =
              deleteSubtaskMutation.isPending && deleteSubtaskMutation.variables === subtask.id;

            return (
              <div
                key={subtask.id}
                className={cn(
                  'flex items-center gap-3 rounded-lg border p-3 transition-all duration-200',
                  subtask.status === 'done' && 'bg-muted/50',
                  isUpdating && 'opacity-60',
                  isDeleting && 'opacity-30 scale-95'
                )}
              >
                <Checkbox
                  checked={subtask.status === 'done'}
                  onCheckedChange={() => handleToggleStatus(subtask)}
                  disabled={isUpdating || isDeleting}
                />

                <div className="flex-1">
                  <p
                    className={cn(
                      'text-sm transition-all',
                      subtask.status === 'done' && 'line-through text-muted-foreground'
                    )}
                  >
                    {subtask.title}
                  </p>
                  {subtask.description && (
                    <p className="text-xs text-muted-foreground line-clamp-1">
                      {subtask.description}
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  {isUpdating ? (
                    <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                  ) : (
                    getStatusIcon(subtask.status)
                  )}

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0"
                        disabled={isUpdating || isDeleting}
                      >
                        {isDeleting ? (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                          <MoreHorizontal className="h-3 w-3" />
                        )}
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        onClick={() => window.open(`/tasks/${subtask.id}`, '_blank')}
                      >
                        <Edit className="mr-2 h-3 w-3" />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        className="text-destructive"
                        onClick={() => handleDeleteSubtask(subtask.id)}
                      >
                        <Trash2 className="mr-2 h-3 w-3" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create subtask dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Create Subtask</DialogTitle>
            <DialogDescription>
              Add a new subtask to break down this task into smaller pieces.
            </DialogDescription>
          </DialogHeader>

          <div className="py-4">
            <Input
              placeholder="Subtask title"
              value={newSubtaskTitle}
              onChange={(e) => setNewSubtaskTitle(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !createSubtaskMutation.isPending) {
                  handleCreateSubtask();
                }
              }}
              disabled={createSubtaskMutation.isPending}
            />
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowCreateDialog(false);
                setNewSubtaskTitle('');
              }}
              disabled={createSubtaskMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateSubtask}
              disabled={!newSubtaskTitle.trim() || createSubtaskMutation.isPending}
            >
              {createSubtaskMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
