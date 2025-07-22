'use client';

import { useState } from 'react';
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
  DialogTrigger,
} from '@/components/ui/dialog';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Calendar } from '@/components/ui/calendar';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';
import {
  Timer,
  Play,
  Pause,
  StopCircle,
  Clock,
  CalendarIcon,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { Task } from '@/lib/api/tasks';
import { useToastContext } from '@/contexts/toast-context';
import { ApiClient } from '@/lib/api-client';

interface TimeTrackingProps {
  task: Task;
  onTimeLogged?: () => void;
}

export function TimeTracking({ task, onTimeLogged }: TimeTrackingProps) {
  const { toast } = useToastContext();
  const [isTimerRunning, setIsTimerRunning] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [timerInterval, setTimerInterval] = useState<NodeJS.Timeout | null>(null);

  // Manual time entry
  const [showLogDialog, setShowLogDialog] = useState(false);
  const [manualHours, setManualHours] = useState('');
  const [description, setDescription] = useState('');
  const [logDate, setLogDate] = useState<Date>(new Date());
  const [isLogging, setIsLogging] = useState(false);

  // Start timer
  const startTimer = () => {
    setIsTimerRunning(true);
    const startTime = Date.now() - elapsedTime;

    const interval = setInterval(() => {
      setElapsedTime(Date.now() - startTime);
    }, 1000);

    setTimerInterval(interval);
  };

  // Pause timer
  const pauseTimer = () => {
    setIsTimerRunning(false);
    if (timerInterval) {
      clearInterval(timerInterval);
      setTimerInterval(null);
    }
  };

  // Stop and log time
  const stopAndLogTime = async () => {
    pauseTimer();

    if (elapsedTime === 0) return;

    const hours = elapsedTime / (1000 * 60 * 60);

    try {
      setIsLogging(true);

      // Call API to log time
      await ApiClient.fetchJSON(ApiClient.buildUrl(`/tasks/${task.id}/time`), {
        method: 'POST',
        body: JSON.stringify({
          hours_to_add: parseFloat(hours.toFixed(2)),
        }),
      });

      toast({
        title: 'Time logged',
        description: `Logged ${formatTime(elapsedTime)} to this task`,
      });

      // Reset timer
      setElapsedTime(0);

      if (onTimeLogged) {
        onTimeLogged();
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to log time. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsLogging(false);
    }
  };

  // Log manual time entry
  const logManualTime = async () => {
    const hours = parseFloat(manualHours);

    if (isNaN(hours) || hours <= 0) {
      toast({
        title: 'Invalid input',
        description: 'Please enter a valid number of hours',
        variant: 'destructive',
      });
      return;
    }

    try {
      setIsLogging(true);

      // Call the more detailed analytics endpoint
      await ApiClient.fetchJSON(ApiClient.buildUrl(`/analytics/tasks/${task.id}/time-log`), {
        method: 'POST',
        body: JSON.stringify({
          hours,
          description: description || undefined,
          logged_at: logDate.toISOString(),
        }),
      });

      toast({
        title: 'Time logged',
        description: `Logged ${hours} hours to this task`,
      });

      // Reset form
      setManualHours('');
      setDescription('');
      setLogDate(new Date());
      setShowLogDialog(false);

      if (onTimeLogged) {
        onTimeLogged();
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to log time. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsLogging(false);
    }
  };

  // Format elapsed time
  const formatTime = (milliseconds: number): string => {
    const totalSeconds = Math.floor(milliseconds / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    return `${hours.toString().padStart(2, '0')}:${minutes
      .toString()
      .padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  const formatHoursDisplay = (hours: number): string => {
    if (hours === 0) return '0h';
    if (hours < 1) return `${Math.round(hours * 60)}m`;
    const wholeHours = Math.floor(hours);
    const minutes = Math.round((hours - wholeHours) * 60);
    if (minutes === 0) return `${wholeHours}h`;
    return `${wholeHours}h ${minutes}m`;
  };

  return (
    <div className="space-y-4">
      {/* Quick Timer */}
      <div className="rounded-lg border p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Timer className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="font-medium">Quick Timer</p>
              <p className="text-2xl font-mono">{formatTime(elapsedTime)}</p>
            </div>
          </div>

          <div className="flex gap-2">
            {!isTimerRunning && elapsedTime === 0 ? (
              <Button onClick={startTimer} size="sm">
                <Play className="mr-2 h-4 w-4" />
                Start
              </Button>
            ) : isTimerRunning ? (
              <>
                <Button onClick={pauseTimer} size="sm" variant="outline">
                  <Pause className="mr-2 h-4 w-4" />
                  Pause
                </Button>
                <Button onClick={stopAndLogTime} size="sm" variant="default" disabled={isLogging}>
                  {isLogging ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <StopCircle className="mr-2 h-4 w-4" />
                  )}
                  Stop & Log
                </Button>
              </>
            ) : (
              <>
                <Button onClick={startTimer} size="sm" variant="outline">
                  <Play className="mr-2 h-4 w-4" />
                  Resume
                </Button>
                <Button onClick={stopAndLogTime} size="sm" variant="default" disabled={isLogging}>
                  {isLogging ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <StopCircle className="mr-2 h-4 w-4" />
                  )}
                  Log Time
                </Button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Manual Time Entry */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">
            Total logged: {formatHoursDisplay(task.actual_hours || 0)}
            {task.estimated_hours && (
              <span className="ml-2">/ {formatHoursDisplay(task.estimated_hours)} estimated</span>
            )}
          </span>
        </div>

        <Dialog open={showLogDialog} onOpenChange={setShowLogDialog}>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm">
              <Clock className="mr-2 h-4 w-4" />
              Log Time
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Log Time</DialogTitle>
              <DialogDescription>Manually log time spent on this task.</DialogDescription>
            </DialogHeader>

            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="hours">Hours *</Label>
                <Input
                  id="hours"
                  type="number"
                  step="0.25"
                  min="0"
                  placeholder="e.g., 2.5"
                  value={manualHours}
                  onChange={(e) => setManualHours(e.target.value)}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="What did you work on?"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                />
              </div>

              <div className="grid gap-2">
                <Label>Date</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className={cn(
                        'justify-start text-left font-normal',
                        !logDate && 'text-muted-foreground'
                      )}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {logDate ? format(logDate, 'PPP') : <span>Pick a date</span>}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0">
                    <Calendar
                      mode="single"
                      selected={logDate}
                      onSelect={(date) => date && setLogDate(date)}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setShowLogDialog(false)}>
                Cancel
              </Button>
              <Button onClick={logManualTime} disabled={isLogging}>
                {isLogging && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Log Time
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Progress indicator */}
      {task.estimated_hours && task.estimated_hours > 0 && (
        <div className="rounded-lg border p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Time Progress</span>
            <span className="text-sm text-muted-foreground">
              {Math.round(((task.actual_hours || 0) / task.estimated_hours) * 100)}%
            </span>
          </div>
          <div className="h-2 bg-secondary rounded-full overflow-hidden">
            <div
              className={cn(
                'h-full transition-all',
                (task.actual_hours || 0) > task.estimated_hours ? 'bg-orange-500' : 'bg-primary'
              )}
              style={{
                width: `${Math.min(((task.actual_hours || 0) / task.estimated_hours) * 100, 100)}%`,
              }}
            />
          </div>
          {(task.actual_hours || 0) > task.estimated_hours && (
            <Alert className="mt-2">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="text-xs">
                This task has exceeded its estimated time by{' '}
                {formatHoursDisplay((task.actual_hours || 0) - task.estimated_hours)}
              </AlertDescription>
            </Alert>
          )}
        </div>
      )}
    </div>
  );
}
