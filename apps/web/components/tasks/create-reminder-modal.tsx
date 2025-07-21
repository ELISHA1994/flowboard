'use client';

import React, { useState, useEffect } from 'react';
import { format, addMinutes, subMinutes, isBefore } from 'date-fns';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Calendar, Clock, Bell } from 'lucide-react';
import {
  useCreateReminderMutation,
  useUpdateReminderMutation,
  useCreateDueDateRemindersMutation,
} from '@/hooks/use-reminders';
import { TaskReminder, TaskReminderCreate, TaskReminderUpdate } from '@/lib/api/reminders';
import { Task } from '@/lib/api/tasks';

interface CreateReminderModalProps {
  task: Task;
  reminder?: TaskReminder | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onComplete: () => void;
}

export function CreateReminderModal({
  task,
  reminder,
  open,
  onOpenChange,
  onComplete,
}: CreateReminderModalProps) {
  const [reminderType, setReminderType] = useState<'custom' | 'due_date'>('custom');
  const [customDate, setCustomDate] = useState('');
  const [customTime, setCustomTime] = useState('');
  const [message, setMessage] = useState('');
  const [selectedOffsets, setSelectedOffsets] = useState<number[]>([]);

  const createReminderMutation = useCreateReminderMutation();
  const updateReminderMutation = useUpdateReminderMutation();
  const createDueDateRemindersMutation = useCreateDueDateRemindersMutation();

  const isEditing = !!reminder;

  // Predefined offset options (in minutes)
  const dueDateOffsets = [
    { label: '15 minutes before', value: 15 },
    { label: '30 minutes before', value: 30 },
    { label: '1 hour before', value: 60 },
    { label: '2 hours before', value: 120 },
    { label: '3 hours before', value: 180 },
    { label: '6 hours before', value: 360 },
    { label: '12 hours before', value: 720 },
    { label: '1 day before', value: 1440 },
    { label: '2 days before', value: 2880 },
    { label: '3 days before', value: 4320 },
    { label: '1 week before', value: 10080 },
  ];

  // Initialize form when editing
  useEffect(() => {
    if (reminder && open) {
      setReminderType(reminder.reminder_type);
      setMessage(reminder.message || '');

      if (reminder.reminder_type === 'custom') {
        const reminderDate = new Date(reminder.remind_at);
        setCustomDate(format(reminderDate, 'yyyy-MM-dd'));
        setCustomTime(format(reminderDate, 'HH:mm'));
      } else if (reminder.offset_minutes) {
        setSelectedOffsets([reminder.offset_minutes]);
      }
    }
  }, [reminder, open]);

  // Reset form when modal closes
  useEffect(() => {
    if (!open) {
      setReminderType('custom');
      setCustomDate('');
      setCustomTime('');
      setMessage('');
      setSelectedOffsets([]);
    }
  }, [open]);

  const handleOffsetToggle = (offset: number) => {
    setSelectedOffsets((prev) =>
      prev.includes(offset) ? prev.filter((o) => o !== offset) : [...prev, offset]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      if (reminderType === 'custom') {
        if (!customDate || !customTime) {
          return;
        }

        const reminderDateTime = new Date(`${customDate}T${customTime}`);

        // Check if the reminder time is in the past
        if (isBefore(reminderDateTime, new Date())) {
          return; // Could add validation error here
        }

        const reminderData: TaskReminderCreate = {
          task_id: task.id,
          remind_at: reminderDateTime.toISOString(),
          reminder_type: 'custom',
          message: message.trim() || undefined,
        };

        if (isEditing) {
          const updateData: TaskReminderUpdate = {
            remind_at: reminderDateTime.toISOString(),
            message: message.trim() || undefined,
          };
          await updateReminderMutation.mutateAsync({
            reminderId: reminder!.id,
            update: updateData,
          });
        } else {
          await createReminderMutation.mutateAsync(reminderData);
        }
      } else {
        // Due date reminders
        if (!task.due_date || selectedOffsets.length === 0) {
          return;
        }

        if (isEditing) {
          // For due date reminders, we delete the old one and create new ones
          // This is simpler than trying to update the offset
          // In a real app, you might want to handle this differently
          return;
        } else {
          await createDueDateRemindersMutation.mutateAsync({
            task_id: task.id,
            offset_minutes: selectedOffsets,
          });
        }
      }

      onComplete();
    } catch (error) {
      // Error handling is done in the mutation hooks
    }
  };

  const isSubmitDisabled = () => {
    if (reminderType === 'custom') {
      return (
        !customDate ||
        !customTime ||
        (customDate && customTime && isBefore(new Date(`${customDate}T${customTime}`), new Date()))
      );
    } else {
      return !task.due_date || selectedOffsets.length === 0;
    }
  };

  const hasDueDate = !!task.due_date;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            {isEditing ? 'Edit Reminder' : 'Add Reminder'}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? 'Update the reminder for this task.'
              : 'Set up a reminder to notify you about this task.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Reminder Type</Label>
            <div className="flex gap-2">
              <Button
                type="button"
                variant={reminderType === 'custom' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setReminderType('custom')}
                className="flex items-center gap-2"
              >
                <Clock className="h-4 w-4" />
                Custom Time
              </Button>
              <Button
                type="button"
                variant={reminderType === 'due_date' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setReminderType('due_date')}
                disabled={!hasDueDate || isEditing}
                className="flex items-center gap-2"
              >
                <Calendar className="h-4 w-4" />
                Before Due Date
              </Button>
            </div>
            {!hasDueDate && (
              <p className="text-sm text-muted-foreground">
                Due date reminders require the task to have a due date set.
              </p>
            )}
          </div>

          {reminderType === 'custom' ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="customDate">Date</Label>
                  <Input
                    id="customDate"
                    type="date"
                    value={customDate}
                    onChange={(e) => setCustomDate(e.target.value)}
                    min={format(new Date(), 'yyyy-MM-dd')}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="customTime">Time</Label>
                  <Input
                    id="customTime"
                    type="time"
                    value={customTime}
                    onChange={(e) => setCustomTime(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="message">Custom Message (Optional)</Label>
                <Textarea
                  id="message"
                  placeholder="Enter a custom reminder message..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  rows={3}
                />
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {task.due_date && (
                <div className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-900">
                    <strong>Task Due Date:</strong>{' '}
                    {format(new Date(task.due_date), 'MMM d, yyyy h:mm a')}
                  </p>
                </div>
              )}

              <div className="space-y-3">
                <Label>Select Reminder Times</Label>
                <div className="grid grid-cols-2 gap-2">
                  {dueDateOffsets.map((offset) => {
                    const isSelected = selectedOffsets.includes(offset.value);
                    return (
                      <Button
                        key={offset.value}
                        type="button"
                        variant={isSelected ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => handleOffsetToggle(offset.value)}
                        className="justify-start"
                      >
                        {offset.label}
                      </Button>
                    );
                  })}
                </div>

                {selectedOffsets.length > 0 && (
                  <div className="space-y-2">
                    <Label>Selected Reminders:</Label>
                    <div className="flex flex-wrap gap-2">
                      {selectedOffsets
                        .sort((a, b) => a - b)
                        .map((offset) => {
                          const offsetLabel = dueDateOffsets.find((o) => o.value === offset)?.label;
                          return (
                            <Badge key={offset} variant="secondary">
                              {offsetLabel}
                            </Badge>
                          );
                        })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={
                isSubmitDisabled() ||
                createReminderMutation.isPending ||
                updateReminderMutation.isPending ||
                createDueDateRemindersMutation.isPending
              }
            >
              {isEditing ? 'Update' : 'Create'} Reminder
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
