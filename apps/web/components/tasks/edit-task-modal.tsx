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
import { AlertCircle, Loader2, Trash2 } from 'lucide-react';
import { Task, UpdateTaskRequest } from '@/lib/api/tasks';
import { useUpdateTaskMutation, useDeleteTaskMutation } from '@/hooks/use-tasks-query';
import { format, parseISO } from 'date-fns';

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

  const [formData, setFormData] = useState<UpdateTaskRequest>({
    title: '',
    description: '',
    status: 'todo',
    priority: 'medium',
    due_date: '',
    start_date: '',
    estimated_hours: undefined,
  });

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
      });
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
