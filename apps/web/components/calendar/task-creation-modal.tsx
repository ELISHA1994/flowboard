'use client';

import React, { useState, useEffect } from 'react';
import { SlotInfo } from 'react-big-calendar';
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
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, CalendarDays, Clock, Loader2 } from 'lucide-react';

import { Task, TaskStatus, TaskPriority } from '@/lib/api/tasks';
import { useCreateTaskFromCalendar } from '@/hooks/use-calendar-tasks';
import { useProjectsQuery } from '@/hooks/use-projects-query';
import { useCategoriesQuery } from '@/hooks/use-categories-query';
import { createTaskFromSlot } from '@/lib/calendar/calendar-utils';
import { format } from 'date-fns';

interface TaskCreationModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  slotInfo: SlotInfo | null;
  onSuccess?: (task: Task) => void;
}

const statusOptions: { value: TaskStatus; label: string }[] = [
  { value: 'todo', label: 'To Do' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'done', label: 'Done' },
];

const priorityOptions: { value: TaskPriority; label: string }[] = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'urgent', label: 'Urgent' },
];

export function TaskCreationModal({
  open,
  onOpenChange,
  slotInfo,
  onSuccess,
}: TaskCreationModalProps) {
  // Form state
  const [formData, setFormData] = useState<Partial<Task>>({
    title: '',
    description: '',
    status: 'todo',
    priority: 'medium',
  });
  const [isAllDay, setIsAllDay] = useState(false);
  const [error, setError] = useState('');

  // Data fetching
  const { data: projectsData } = useProjectsQuery();
  const { data: categoriesData } = useCategoriesQuery();
  const projects = projectsData?.projects || [];
  const categories = categoriesData || [];

  // Mutation
  const createTaskMutation = useCreateTaskFromCalendar();

  // Initialize form data when slot changes
  useEffect(() => {
    if (slotInfo && open) {
      const baseData = createTaskFromSlot(slotInfo);
      const calculatedIsAllDay = !baseData.start_date;

      setFormData((prev) => ({
        ...prev,
        ...baseData,
        title: prev.title || '',
        description: prev.description || '',
      }));
      setIsAllDay(calculatedIsAllDay);
      setError('');
    }
  }, [slotInfo, open]);

  // Form handlers
  const updateFormData = (field: keyof Task, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setError('');
  };

  const handleAllDayToggle = (checked: boolean) => {
    setIsAllDay(checked);

    if (checked) {
      // Convert to all-day event
      updateFormData('start_date', undefined);
      updateFormData('estimated_hours', undefined);
    } else if (slotInfo) {
      // Convert back to timed event
      updateFormData('start_date', slotInfo.start.toISOString());
      const durationHours = (slotInfo.end.getTime() - slotInfo.start.getTime()) / (1000 * 60 * 60);
      updateFormData('estimated_hours', Math.round(durationHours * 2) / 2);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!formData.title?.trim()) {
      setError('Task title is required');
      return;
    }

    if (!formData.due_date) {
      setError('Due date is required');
      return;
    }

    try {
      const newTask = await createTaskMutation.mutateAsync(formData);
      onSuccess?.(newTask);
      handleCancel(); // Reset form
    } catch (err: any) {
      setError(err.message || 'Failed to create task');
    }
  };

  const handleCancel = () => {
    setFormData({
      title: '',
      description: '',
      status: 'todo',
      priority: 'medium',
    });
    setIsAllDay(false);
    setError('');
    createTaskMutation.reset();
    onOpenChange(false);
  };

  // Format date display
  const formatSlotInfo = () => {
    if (!slotInfo) return '';

    if (isAllDay) {
      return format(slotInfo.end, 'EEEE, MMMM d, yyyy');
    } else {
      const startTime = format(slotInfo.start, 'h:mm a');
      const endTime = format(slotInfo.end, 'h:mm a');
      const date = format(slotInfo.start, 'EEEE, MMMM d, yyyy');
      return `${date} from ${startTime} to ${endTime}`;
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Create New Task</DialogTitle>
            <DialogDescription className="flex items-center gap-2">
              <CalendarDays className="h-4 w-4" />
              {formatSlotInfo()}
            </DialogDescription>
          </DialogHeader>

          {error && (
            <Alert variant="destructive" className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="grid gap-4 py-4">
            {/* Task Title */}
            <div className="grid gap-2">
              <Label htmlFor="title">Task Title *</Label>
              <Input
                id="title"
                value={formData.title || ''}
                onChange={(e) => updateFormData('title', e.target.value)}
                placeholder="Enter task title..."
                disabled={createTaskMutation.isPending}
                required
              />
            </div>

            {/* Description */}
            <div className="grid gap-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description || ''}
                onChange={(e) => updateFormData('description', e.target.value)}
                placeholder="Add task description..."
                disabled={createTaskMutation.isPending}
                rows={3}
              />
            </div>

            {/* All Day Toggle */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                <Label htmlFor="all-day">All Day Task</Label>
              </div>
              <Switch
                id="all-day"
                checked={isAllDay}
                onCheckedChange={handleAllDayToggle}
                disabled={createTaskMutation.isPending}
              />
            </div>

            {/* Estimated Hours (shown only for timed tasks) */}
            {!isAllDay && (
              <div className="grid gap-2">
                <Label htmlFor="estimated-hours">Estimated Hours</Label>
                <Input
                  id="estimated-hours"
                  type="number"
                  min="0.5"
                  max="24"
                  step="0.5"
                  value={formData.estimated_hours || ''}
                  onChange={(e) =>
                    updateFormData('estimated_hours', parseFloat(e.target.value) || undefined)
                  }
                  placeholder="e.g., 2.5"
                  disabled={createTaskMutation.isPending}
                />
              </div>
            )}

            {/* Status and Priority */}
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="status">Status</Label>
                <Select
                  value={formData.status || 'todo'}
                  onValueChange={(value: TaskStatus) => updateFormData('status', value)}
                  disabled={createTaskMutation.isPending}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select status" />
                  </SelectTrigger>
                  <SelectContent>
                    {statusOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="priority">Priority</Label>
                <Select
                  value={formData.priority || 'medium'}
                  onValueChange={(value: TaskPriority) => updateFormData('priority', value)}
                  disabled={createTaskMutation.isPending}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select priority" />
                  </SelectTrigger>
                  <SelectContent>
                    {priorityOptions.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Project Selection */}
            {projects.length > 0 && (
              <div className="grid gap-2">
                <Label htmlFor="project">Project</Label>
                <Select
                  value={formData.project_id || ''}
                  onValueChange={(value) => updateFormData('project_id', value || undefined)}
                  disabled={createTaskMutation.isPending}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select project (optional)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">No project</SelectItem>
                    {projects.map((project) => (
                      <SelectItem key={project.id} value={project.id}>
                        {project.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={createTaskMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={createTaskMutation.isPending || !formData.title?.trim()}
            >
              {createTaskMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create Task
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default TaskCreationModal;
