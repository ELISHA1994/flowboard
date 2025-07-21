'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import { Badge } from '@/components/ui/badge';
import {
  GitBranch,
  Plus,
  X,
  CheckCircle2,
  Circle,
  Clock,
  XCircle,
  AlertCircle,
  Search,
  Loader2,
  ArrowRight,
} from 'lucide-react';
import { Task, TasksService } from '@/lib/api/tasks';
import { useToastContext } from '@/contexts/toast-context';
import { cn } from '@/lib/utils';
import { ScrollArea } from '@/components/ui/scroll-area';

interface TaskDependenciesProps {
  task: Task;
  onUpdate?: () => void;
}

interface Dependency {
  id: string;
  task_id: string;
  depends_on_id: string;
  depends_on: Task;
  created_at: string;
}

export function TaskDependencies({ task, onUpdate }: TaskDependenciesProps) {
  const { toast } = useToastContext();
  const [dependencies, setDependencies] = useState<Dependency[]>(task.dependencies || []);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Task[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [adding, setAdding] = useState(false);

  // Update dependencies when task changes
  useEffect(() => {
    setDependencies(task.dependencies || []);
  }, [task.dependencies]);

  // Search for tasks to add as dependencies
  const searchTasks = async (query: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    try {
      setSearching(true);
      const results = await TasksService.searchTasks({
        query,
        limit: 10,
      });

      // Filter out current task and existing dependencies
      const existingDepIds = dependencies.map((dep) => dep.depends_on_id);
      const filteredResults = results.filter(
        (t) => t.id !== task.id && !existingDepIds.includes(t.id)
      );

      setSearchResults(filteredResults);
    } catch (error) {
      console.error('Failed to search tasks:', error);
    } finally {
      setSearching(false);
    }
  };

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      searchTasks(searchQuery);
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Add dependency
  const addDependency = async () => {
    if (!selectedTask) return;

    try {
      setAdding(true);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/tasks/${task.id}/dependencies`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
          body: JSON.stringify({
            depends_on_id: selectedTask.id,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to add dependency');
      }

      const newDependency = await response.json();
      setDependencies([...dependencies, newDependency]);

      toast({
        title: 'Dependency added',
        description: `This task now depends on "${selectedTask.title}"`,
      });

      setShowAddDialog(false);
      setSelectedTask(null);
      setSearchQuery('');
      setSearchResults([]);

      if (onUpdate) {
        onUpdate();
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to add dependency. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setAdding(false);
    }
  };

  // Remove dependency
  const removeDependency = async (dependencyId: string) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/tasks/${task.id}/dependencies/${dependencyId}`,
        {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to remove dependency');
      }

      setDependencies(dependencies.filter((dep) => dep.id !== dependencyId));

      toast({
        title: 'Dependency removed',
        description: 'The dependency has been removed successfully.',
      });

      if (onUpdate) {
        onUpdate();
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to remove dependency.',
        variant: 'destructive',
      });
    }
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

  // Check if task is blocked
  const isTaskBlocked = dependencies.some(
    (dep) => dep.depends_on.status !== 'done' && dep.depends_on.status !== 'cancelled'
  );

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <GitBranch className="h-4 w-4 text-muted-foreground" />
          <h4 className="text-sm font-medium">Dependencies</h4>
          {dependencies.length > 0 && (
            <Badge variant="secondary" className="text-xs">
              {dependencies.length}
            </Badge>
          )}
        </div>

        <Button variant="outline" size="sm" onClick={() => setShowAddDialog(true)}>
          <Plus className="mr-1 h-3 w-3" />
          Add
        </Button>
      </div>

      {/* Blocked warning */}
      {isTaskBlocked && (
        <div className="rounded-lg border border-orange-200 bg-orange-50 p-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-orange-600" />
            <p className="text-sm text-orange-800">
              This task is blocked by incomplete dependencies
            </p>
          </div>
        </div>
      )}

      {/* Dependencies list */}
      {dependencies.length === 0 ? (
        <div className="rounded-lg border border-dashed p-4 text-center">
          <GitBranch className="mx-auto h-8 w-8 text-muted-foreground/50" />
          <p className="mt-2 text-sm text-muted-foreground">No dependencies</p>
          <p className="text-xs text-muted-foreground">Add tasks that need to be completed first</p>
        </div>
      ) : (
        <div className="space-y-2">
          {dependencies.map((dependency) => (
            <div
              key={dependency.id}
              className={cn(
                'flex items-center gap-3 rounded-lg border p-3',
                dependency.depends_on.status === 'done' && 'bg-muted/50'
              )}
            >
              {getStatusIcon(dependency.depends_on.status)}

              <div className="flex-1">
                <a
                  href={`/tasks/${dependency.depends_on.id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm font-medium hover:underline"
                >
                  {dependency.depends_on.title}
                </a>
                <p className="text-xs text-muted-foreground">
                  {dependency.depends_on.status.replace('_', ' ')} • Due{' '}
                  {dependency.depends_on.due_date
                    ? new Date(dependency.depends_on.due_date).toLocaleDateString()
                    : 'anytime'}
                </p>
              </div>

              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                onClick={() => removeDependency(dependency.id)}
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
          ))}
        </div>
      )}

      {/* Add dependency dialog */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Add Dependency</DialogTitle>
            <DialogDescription>
              Select a task that must be completed before this task can begin.
            </DialogDescription>
          </DialogHeader>

          <div className="py-4">
            {/* Search input */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search for tasks..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>

            {/* Search results */}
            <ScrollArea className="mt-4 max-h-[300px]">
              {searching ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                </div>
              ) : searchResults.length === 0 && searchQuery ? (
                <div className="py-8 text-center">
                  <p className="text-sm text-muted-foreground">
                    No tasks found matching "{searchQuery}"
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {searchResults.map((result) => (
                    <div
                      key={result.id}
                      className={cn(
                        'flex cursor-pointer items-center gap-3 rounded-lg border p-3 transition-colors hover:bg-accent',
                        selectedTask?.id === result.id && 'border-primary bg-accent'
                      )}
                      onClick={() => setSelectedTask(result)}
                    >
                      {getStatusIcon(result.status)}
                      <div className="flex-1">
                        <p className="text-sm font-medium">{result.title}</p>
                        <p className="text-xs text-muted-foreground">
                          {result.status.replace('_', ' ')} • Priority: {result.priority}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>

            {/* Selected task preview */}
            {selectedTask && (
              <div className="mt-4 rounded-lg bg-muted p-3">
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-medium">Selected:</span>
                  <span>{selectedTask.title}</span>
                  <ArrowRight className="h-3 w-3 text-muted-foreground" />
                  <span className="text-muted-foreground">blocks</span>
                  <ArrowRight className="h-3 w-3 text-muted-foreground" />
                  <span>{task.title}</span>
                </div>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowAddDialog(false);
                setSelectedTask(null);
                setSearchQuery('');
                setSearchResults([]);
              }}
            >
              Cancel
            </Button>
            <Button onClick={addDependency} disabled={!selectedTask || adding}>
              {adding && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Add Dependency
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
