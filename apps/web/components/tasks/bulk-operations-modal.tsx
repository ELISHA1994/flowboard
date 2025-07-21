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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  CheckCircle2,
  Clock,
  Circle,
  XCircle,
  Flag,
  Calendar,
  Users,
  Tag,
  Folder,
  AlertCircle,
  Hash,
} from 'lucide-react';
import { TaskStatus, TaskPriority, UpdateTaskRequest } from '@/lib/api/tasks';
import { Project } from '@/lib/api/projects';
import { Category } from '@/lib/api/categories';
import { Tag as TagType } from '@/lib/api/tags';
import { format } from 'date-fns';
import { Calendar as CalendarComponent } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { cn } from '@/lib/utils';

export interface BulkOperation {
  field: keyof UpdateTaskRequest;
  value: any;
  label: string;
}

interface BulkOperationsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedCount: number;
  onApplyOperations: (operations: BulkOperation[]) => void;
  projects: Project[];
  categories: Category[];
  tags: TagType[];
  users?: Array<{ id: string; username: string; email: string }>;
}

export function BulkOperationsModal({
  open,
  onOpenChange,
  selectedCount,
  onApplyOperations,
  projects,
  categories,
  tags,
  users = [],
}: BulkOperationsModalProps) {
  const [selectedOperations, setSelectedOperations] = useState<BulkOperation[]>([]);
  const [activeTab, setActiveTab] = useState('status');

  // Operation states
  const [status, setStatus] = useState<TaskStatus | ''>('');
  const [priority, setPriority] = useState<TaskPriority | ''>('');
  const [projectId, setProjectId] = useState<string>('');
  const [assignedToId, setAssignedToId] = useState<string>('');
  const [dueDate, setDueDate] = useState<Date | undefined>();
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  const handleAddOperation = (field: keyof UpdateTaskRequest, value: any, label: string) => {
    const existingIndex = selectedOperations.findIndex((op) => op.field === field);
    const newOperation: BulkOperation = { field, value, label };

    if (existingIndex >= 0) {
      const updated = [...selectedOperations];
      updated[existingIndex] = newOperation;
      setSelectedOperations(updated);
    } else {
      setSelectedOperations([...selectedOperations, newOperation]);
    }
  };

  const handleRemoveOperation = (field: keyof UpdateTaskRequest) => {
    setSelectedOperations(selectedOperations.filter((op) => op.field !== field));

    // Reset the corresponding state
    switch (field) {
      case 'status':
        setStatus('');
        break;
      case 'priority':
        setPriority('');
        break;
      case 'project_id':
        setProjectId('');
        break;
      case 'assigned_to_id':
        setAssignedToId('');
        break;
      case 'due_date':
        setDueDate(undefined);
        break;
      case 'category_ids':
        setSelectedCategories([]);
        break;
      case 'tag_ids':
        setSelectedTags([]);
        break;
    }
  };

  const handleApply = () => {
    onApplyOperations(selectedOperations);
    onOpenChange(false);
    // Reset state
    setSelectedOperations([]);
    setStatus('');
    setPriority('');
    setProjectId('');
    setAssignedToId('');
    setDueDate(undefined);
    setSelectedCategories([]);
    setSelectedTags([]);
  };

  const getStatusIcon = (status: TaskStatus) => {
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

  const getPriorityColor = (priority: TaskPriority) => {
    switch (priority) {
      case 'urgent':
        return 'text-red-600';
      case 'high':
        return 'text-orange-600';
      case 'medium':
        return 'text-yellow-600';
      case 'low':
        return 'text-green-600';
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle>Bulk Operations</DialogTitle>
          <DialogDescription>
            Apply changes to {selectedCount} selected task{selectedCount !== 1 ? 's' : ''}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Selected Operations Summary */}
          {selectedOperations.length > 0 && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <div className="space-y-2">
                  <p className="font-medium">Operations to apply:</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedOperations.map((op) => (
                      <Badge
                        key={op.field}
                        variant="secondary"
                        className="cursor-pointer"
                        onClick={() => handleRemoveOperation(op.field)}
                      >
                        {op.label}
                        <XCircle className="ml-1 h-3 w-3" />
                      </Badge>
                    ))}
                  </div>
                </div>
              </AlertDescription>
            </Alert>
          )}

          {/* Operation Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="status">Status & Priority</TabsTrigger>
              <TabsTrigger value="assignment">Assignment</TabsTrigger>
              <TabsTrigger value="organization">Organization</TabsTrigger>
              <TabsTrigger value="dates">Dates</TabsTrigger>
            </TabsList>

            <ScrollArea className="h-[300px] mt-4">
              <TabsContent value="status" className="space-y-4">
                <div className="space-y-2">
                  <Label>Change Status</Label>
                  <Select
                    value={status}
                    onValueChange={(value: TaskStatus) => {
                      setStatus(value);
                      handleAddOperation('status', value, `Status: ${value.replace('_', ' ')}`);
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select new status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="todo">
                        <div className="flex items-center gap-2">
                          {getStatusIcon('todo')}
                          To Do
                        </div>
                      </SelectItem>
                      <SelectItem value="in_progress">
                        <div className="flex items-center gap-2">
                          {getStatusIcon('in_progress')}
                          In Progress
                        </div>
                      </SelectItem>
                      <SelectItem value="done">
                        <div className="flex items-center gap-2">
                          {getStatusIcon('done')}
                          Done
                        </div>
                      </SelectItem>
                      <SelectItem value="cancelled">
                        <div className="flex items-center gap-2">
                          {getStatusIcon('cancelled')}
                          Cancelled
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Change Priority</Label>
                  <Select
                    value={priority}
                    onValueChange={(value: TaskPriority) => {
                      setPriority(value);
                      handleAddOperation('priority', value, `Priority: ${value}`);
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select new priority" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="urgent">
                        <div className="flex items-center gap-2">
                          <Flag className={cn('h-4 w-4', getPriorityColor('urgent'))} />
                          Urgent
                        </div>
                      </SelectItem>
                      <SelectItem value="high">
                        <div className="flex items-center gap-2">
                          <Flag className={cn('h-4 w-4', getPriorityColor('high'))} />
                          High
                        </div>
                      </SelectItem>
                      <SelectItem value="medium">
                        <div className="flex items-center gap-2">
                          <Flag className={cn('h-4 w-4', getPriorityColor('medium'))} />
                          Medium
                        </div>
                      </SelectItem>
                      <SelectItem value="low">
                        <div className="flex items-center gap-2">
                          <Flag className={cn('h-4 w-4', getPriorityColor('low'))} />
                          Low
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </TabsContent>

              <TabsContent value="assignment" className="space-y-4">
                <div className="space-y-2">
                  <Label>Assign To</Label>
                  <Select
                    value={assignedToId}
                    onValueChange={(value) => {
                      setAssignedToId(value);
                      const user = users.find((u) => u.id === value);
                      handleAddOperation(
                        'assigned_to_id',
                        value,
                        `Assigned to: ${user?.username || 'Unassigned'}`
                      );
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select assignee" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="unassigned">
                        <div className="flex items-center gap-2">
                          <Users className="h-4 w-4" />
                          Unassigned
                        </div>
                      </SelectItem>
                      {users.map((user) => (
                        <SelectItem key={user.id} value={user.id}>
                          <div className="flex items-center gap-2">
                            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-muted text-xs">
                              {user.username.substring(0, 2).toUpperCase()}
                            </div>
                            {user.username}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Move to Project</Label>
                  <Select
                    value={projectId}
                    onValueChange={(value) => {
                      setProjectId(value);
                      const project = projects.find((p) => p.id === value);
                      handleAddOperation(
                        'project_id',
                        value,
                        `Project: ${project?.name || 'None'}`
                      );
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select project" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">
                        <div className="flex items-center gap-2">
                          <Folder className="h-4 w-4" />
                          No Project
                        </div>
                      </SelectItem>
                      {projects.map((project) => (
                        <SelectItem key={project.id} value={project.id}>
                          <div className="flex items-center gap-2">
                            <div
                              className="h-4 w-4 rounded-full"
                              style={{ backgroundColor: project.color || '#6366f1' }}
                            />
                            {project.name}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </TabsContent>

              <TabsContent value="organization" className="space-y-4">
                <div className="space-y-2">
                  <Label>Add Categories</Label>
                  <div className="border rounded-lg p-3">
                    <ScrollArea className="h-[120px]">
                      <div className="space-y-2">
                        {categories.map((category) => (
                          <div key={category.id} className="flex items-center space-x-2">
                            <Checkbox
                              id={`bulk-category-${category.id}`}
                              checked={selectedCategories.includes(category.id)}
                              onCheckedChange={(checked) => {
                                if (checked) {
                                  const newCategories = [...selectedCategories, category.id];
                                  setSelectedCategories(newCategories);
                                  handleAddOperation(
                                    'category_ids',
                                    newCategories,
                                    `${newCategories.length} categories`
                                  );
                                } else {
                                  const newCategories = selectedCategories.filter(
                                    (id) => id !== category.id
                                  );
                                  setSelectedCategories(newCategories);
                                  if (newCategories.length > 0) {
                                    handleAddOperation(
                                      'category_ids',
                                      newCategories,
                                      `${newCategories.length} categories`
                                    );
                                  } else {
                                    handleRemoveOperation('category_ids');
                                  }
                                }
                              }}
                            />
                            <label
                              htmlFor={`bulk-category-${category.id}`}
                              className="flex items-center gap-2 cursor-pointer flex-1"
                            >
                              <div
                                className="h-6 w-6 rounded flex items-center justify-center text-xs"
                                style={{
                                  backgroundColor: `${category.color}20`,
                                  color: category.color,
                                }}
                              >
                                {category.icon}
                              </div>
                              {category.name}
                            </label>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Add Tags</Label>
                  <div className="border rounded-lg p-3">
                    <ScrollArea className="h-[120px]">
                      <div className="flex flex-wrap gap-2">
                        {tags.map((tag) => (
                          <Badge
                            key={tag.id}
                            variant={selectedTags.includes(tag.id) ? 'default' : 'outline'}
                            className="cursor-pointer"
                            style={{
                              backgroundColor: selectedTags.includes(tag.id)
                                ? tag.color
                                : `${tag.color}20`,
                              color: selectedTags.includes(tag.id) ? 'white' : tag.color,
                              borderColor: tag.color,
                            }}
                            onClick={() => {
                              if (selectedTags.includes(tag.id)) {
                                const newTags = selectedTags.filter((id) => id !== tag.id);
                                setSelectedTags(newTags);
                                if (newTags.length > 0) {
                                  handleAddOperation('tag_ids', newTags, `${newTags.length} tags`);
                                } else {
                                  handleRemoveOperation('tag_ids');
                                }
                              } else {
                                const newTags = [...selectedTags, tag.id];
                                setSelectedTags(newTags);
                                handleAddOperation('tag_ids', newTags, `${newTags.length} tags`);
                              }
                            }}
                          >
                            <Hash className="h-3 w-3 mr-1" />
                            {tag.name}
                          </Badge>
                        ))}
                      </div>
                    </ScrollArea>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="dates" className="space-y-4">
                <div className="space-y-2">
                  <Label>Set Due Date</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className={cn(
                          'w-full justify-start text-left font-normal',
                          !dueDate && 'text-muted-foreground'
                        )}
                      >
                        <Calendar className="mr-2 h-4 w-4" />
                        {dueDate ? format(dueDate, 'PPP') : 'Pick a date'}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <CalendarComponent
                        mode="single"
                        selected={dueDate}
                        onSelect={(date) => {
                          setDueDate(date);
                          if (date) {
                            handleAddOperation(
                              'due_date',
                              date.toISOString().split('T')[0],
                              `Due: ${format(date, 'MMM d, yyyy')}`
                            );
                          } else {
                            handleRemoveOperation('due_date');
                          }
                        }}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                  {dueDate && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setDueDate(undefined);
                        handleRemoveOperation('due_date');
                      }}
                    >
                      Clear due date
                    </Button>
                  )}
                </div>
              </TabsContent>
            </ScrollArea>
          </Tabs>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleApply} disabled={selectedOperations.length === 0}>
            Apply {selectedOperations.length} Operation{selectedOperations.length !== 1 ? 's' : ''}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
