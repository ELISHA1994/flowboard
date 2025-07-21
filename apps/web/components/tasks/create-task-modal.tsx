'use client';

import { useState } from 'react';
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
import { AlertCircle, Loader2 } from 'lucide-react';
import { CreateTaskRequest } from '@/lib/api/tasks';
import { useCreateTaskMutation } from '@/hooks/use-tasks-query';
import { format } from 'date-fns';

interface CreateTaskModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onTaskCreated?: () => void;
}

export function CreateTaskModal({ open, onOpenChange, onTaskCreated }: CreateTaskModalProps) {
  const router = useRouter();
  const createTaskMutation = useCreateTaskMutation();

  const [formData, setFormData] = useState<CreateTaskRequest>({
    title: '',
    description: '',
    status: 'todo',
    priority: 'medium',
    due_date: '',
    start_date: '',
    estimated_hours: undefined,
  });

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
        });

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
