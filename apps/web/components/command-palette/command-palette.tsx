'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import {
  Command,
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from 'cmdk';
import {
  Home,
  CheckSquare,
  Inbox,
  Calendar,
  FolderOpen,
  BarChart3,
  Settings,
  Plus,
  Search,
  Clock,
  Circle,
  CheckCircle2,
  AlertCircle,
  LogOut,
  User,
  HelpCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/contexts/auth-context';
import { TasksService, Task } from '@/lib/api/tasks';
import { useDebounce } from '@/hooks/use-debounce';
import { SearchService } from '@/lib/api/search';

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [search, setSearch] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [searchResults, setSearchResults] = React.useState<Task[]>([]);
  const [recentTasks, setRecentTasks] = React.useState<Task[]>([]);

  const debouncedSearch = useDebounce(search, 300);

  // Load recent tasks when palette opens
  React.useEffect(() => {
    if (open) {
      loadRecentTasks();
    }
  }, [open]);

  // Search tasks when search query changes
  React.useEffect(() => {
    if (debouncedSearch) {
      searchTasks(debouncedSearch);
    } else {
      setSearchResults([]);
    }
  }, [debouncedSearch]);

  const loadRecentTasks = async () => {
    try {
      const tasks = await TasksService.getRecentTasks(5);
      setRecentTasks(tasks);
    } catch (error) {
      console.error('Failed to load recent tasks:', error);
    }
  };

  const searchTasks = async (query: string) => {
    try {
      setLoading(true);
      const results = await SearchService.searchTasks({
        text: query,
        limit: 5,
      });
      setSearchResults(results.tasks);
    } catch (error) {
      console.error('Failed to search tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const runCommand = React.useCallback(
    (command: () => void) => {
      onOpenChange(false);
      command();
    },
    [onOpenChange]
  );

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'done':
        return <CheckCircle2 className="mr-2 h-4 w-4 text-green-600" />;
      case 'in_progress':
        return <Clock className="mr-2 h-4 w-4 text-blue-600" />;
      default:
        return <Circle className="mr-2 h-4 w-4 text-muted-foreground" />;
    }
  };

  const getPriorityBadge = (priority: string) => {
    return (
      <span
        className={cn(
          'ml-auto text-xs rounded-full px-2 py-0.5',
          priority === 'urgent' && 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400',
          priority === 'high' &&
            'bg-orange-100 text-orange-700 dark:bg-orange-900/20 dark:text-orange-400',
          priority === 'medium' &&
            'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400',
          priority === 'low' &&
            'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400'
        )}
      >
        {priority}
      </span>
    );
  };

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange} className="max-w-2xl">
      <Command className="rounded-lg border shadow-md">
        <CommandInput
          placeholder="Search tasks, navigate, or type a command..."
          value={search}
          onValueChange={setSearch}
        />
        <CommandList>
          <CommandEmpty>{loading ? 'Searching...' : 'No results found.'}</CommandEmpty>

          {/* Search Results */}
          {searchResults.length > 0 && (
            <CommandGroup heading="Search Results">
              {searchResults.map((task) => (
                <CommandItem
                  key={task.id}
                  value={task.title}
                  onSelect={() => runCommand(() => router.push(`/tasks/${task.id}`))}
                  className="flex items-center"
                >
                  {getStatusIcon(task.status)}
                  <span className="flex-1">{task.title}</span>
                  {getPriorityBadge(task.priority)}
                </CommandItem>
              ))}
            </CommandGroup>
          )}

          {/* Recent Tasks - only show when not searching */}
          {!search && recentTasks.length > 0 && (
            <>
              <CommandGroup heading="Recent Tasks">
                {recentTasks.map((task) => (
                  <CommandItem
                    key={task.id}
                    value={`recent-${task.title}`}
                    onSelect={() => runCommand(() => router.push(`/tasks/${task.id}`))}
                    className="flex items-center"
                  >
                    {getStatusIcon(task.status)}
                    <span className="flex-1">{task.title}</span>
                    {getPriorityBadge(task.priority)}
                  </CommandItem>
                ))}
              </CommandGroup>
              <CommandSeparator />
            </>
          )}

          {/* Quick Actions */}
          <CommandGroup heading="Quick Actions">
            <CommandItem
              value="create-task"
              onSelect={() =>
                runCommand(() => {
                  // Trigger new task modal
                  const event = new CustomEvent('open-create-task-modal');
                  window.dispatchEvent(event);
                })
              }
            >
              <Plus className="mr-2 h-4 w-4" />
              <span>Create New Task</span>
            </CommandItem>
          </CommandGroup>

          <CommandSeparator />

          {/* Navigation */}
          <CommandGroup heading="Navigation">
            <CommandItem
              value="dashboard"
              onSelect={() => runCommand(() => router.push('/dashboard'))}
            >
              <Home className="mr-2 h-4 w-4" />
              <span>Dashboard</span>
            </CommandItem>
            <CommandItem value="tasks" onSelect={() => runCommand(() => router.push('/tasks'))}>
              <CheckSquare className="mr-2 h-4 w-4" />
              <span>My Tasks</span>
            </CommandItem>
            <CommandItem value="inbox" onSelect={() => runCommand(() => router.push('/inbox'))}>
              <Inbox className="mr-2 h-4 w-4" />
              <span>Inbox</span>
            </CommandItem>
            <CommandItem
              value="calendar"
              onSelect={() => runCommand(() => router.push('/calendar'))}
            >
              <Calendar className="mr-2 h-4 w-4" />
              <span>Calendar</span>
            </CommandItem>
            <CommandItem
              value="projects"
              onSelect={() => runCommand(() => router.push('/projects'))}
            >
              <FolderOpen className="mr-2 h-4 w-4" />
              <span>Projects</span>
            </CommandItem>
            <CommandItem
              value="analytics"
              onSelect={() => runCommand(() => router.push('/analytics'))}
            >
              <BarChart3 className="mr-2 h-4 w-4" />
              <span>Analytics</span>
            </CommandItem>
          </CommandGroup>

          <CommandSeparator />

          {/* User Actions */}
          <CommandGroup heading="Account">
            <CommandItem value="profile" onSelect={() => runCommand(() => router.push('/profile'))}>
              <User className="mr-2 h-4 w-4" />
              <span>Profile</span>
            </CommandItem>
            <CommandItem
              value="settings"
              onSelect={() => runCommand(() => router.push('/settings'))}
            >
              <Settings className="mr-2 h-4 w-4" />
              <span>Settings</span>
            </CommandItem>
            <CommandItem value="help" onSelect={() => runCommand(() => router.push('/help'))}>
              <HelpCircle className="mr-2 h-4 w-4" />
              <span>Help & Support</span>
            </CommandItem>
            <CommandItem
              value="logout"
              onSelect={() => runCommand(handleLogout)}
              className="text-destructive"
            >
              <LogOut className="mr-2 h-4 w-4" />
              <span>Log out</span>
            </CommandItem>
          </CommandGroup>
        </CommandList>
      </Command>
    </CommandDialog>
  );
}
