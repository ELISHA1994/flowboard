import { Task } from '@/lib/api/tasks';
import {
  startOfDay,
  endOfDay,
  addHours,
  parseISO,
  isValid,
  startOfWeek,
  endOfWeek,
  startOfMonth,
  endOfMonth,
  format,
} from 'date-fns';

// Calendar Event interface for react-big-calendar
export interface CalendarEvent {
  id: string;
  title: string;
  start: Date;
  end: Date;
  allDay: boolean;
  resource: Task; // Full task object for reference
  backgroundColor: string;
  borderColor: string;
  textColor: string;
  priority: string;
  status: string;
  project?: string;
}

// Priority color mapping
export const PRIORITY_COLORS = {
  urgent: {
    background: '#dc2626', // red-600
    border: '#991b1b', // red-800
    text: '#ffffff',
  },
  high: {
    background: '#ea580c', // orange-600
    border: '#c2410c', // orange-700
    text: '#ffffff',
  },
  medium: {
    background: '#2563eb', // blue-600
    border: '#1d4ed8', // blue-700
    text: '#ffffff',
  },
  low: {
    background: '#16a34a', // green-600
    border: '#15803d', // green-700
    text: '#ffffff',
  },
} as const;

// Status color mapping
export const STATUS_COLORS = {
  todo: {
    background: '#6b7280', // gray-500
    border: '#4b5563', // gray-600
    text: '#ffffff',
  },
  in_progress: {
    background: '#f59e0b', // amber-500
    border: '#d97706', // amber-600
    text: '#ffffff',
  },
  done: {
    background: '#10b981', // emerald-500
    border: '#059669', // emerald-600
    text: '#ffffff',
  },
  cancelled: {
    background: '#8b5cf6', // violet-500
    border: '#7c3aed', // violet-600
    text: '#ffffff',
  },
} as const;

/**
 * Convert a Task object to a CalendarEvent
 */
export function taskToCalendarEvent(task: Task): CalendarEvent {
  // Parse dates
  const dueDate = task.due_date ? parseISO(task.due_date) : null;
  const startDate = task.start_date ? parseISO(task.start_date) : null;

  // Determine event start and end times
  let eventStart: Date;
  let eventEnd: Date;
  let allDay = false;

  if (startDate && dueDate) {
    // Task has both start and due date
    eventStart = startDate;
    eventEnd = dueDate;
  } else if (dueDate) {
    // Task has only due date
    if (task.estimated_hours && task.estimated_hours > 0) {
      // Create time block based on estimated hours
      eventEnd = dueDate;
      eventStart = addHours(dueDate, -task.estimated_hours);
    } else {
      // All day event on due date
      eventStart = startOfDay(dueDate);
      eventEnd = endOfDay(dueDate);
      allDay = true;
    }
  } else if (startDate) {
    // Task has only start date
    eventStart = startDate;
    if (task.estimated_hours && task.estimated_hours > 0) {
      eventEnd = addHours(startDate, task.estimated_hours);
    } else {
      eventEnd = addHours(startDate, 1); // Default 1 hour duration
    }
  } else {
    // No dates - create placeholder for today
    eventStart = new Date();
    eventEnd = addHours(eventStart, 1);
    allDay = true;
  }

  // Get colors based on priority
  const priorityColors = PRIORITY_COLORS[task.priority] || PRIORITY_COLORS.medium;

  // Adjust opacity for completed tasks
  let backgroundColor = priorityColors.background;
  let textColor = priorityColors.text;

  if (task.status === 'done') {
    backgroundColor = STATUS_COLORS.done.background;
    textColor = STATUS_COLORS.done.text;
  } else if (task.status === 'cancelled') {
    backgroundColor = STATUS_COLORS.cancelled.background;
    textColor = STATUS_COLORS.cancelled.text;
  }

  return {
    id: task.id,
    title: task.title,
    start: eventStart,
    end: eventEnd,
    allDay,
    resource: task,
    backgroundColor,
    borderColor: priorityColors.border,
    textColor,
    priority: task.priority,
    status: task.status,
    project: task.project?.name,
  };
}

/**
 * Convert multiple tasks to calendar events
 */
export function tasksToCalendarEvents(tasks: Task[]): CalendarEvent[] {
  return tasks.map(taskToCalendarEvent).filter(
    (event) =>
      // Filter out invalid events
      isValid(event.start) && isValid(event.end)
  );
}

/**
 * Get date range for calendar view
 */
export function getCalendarDateRange(date: Date, view: string): { start: Date; end: Date } {
  switch (view) {
    case 'month':
      return {
        start: startOfMonth(date),
        end: endOfMonth(date),
      };
    case 'week':
      return {
        start: startOfWeek(date, { weekStartsOn: 1 }), // Start on Monday
        end: endOfWeek(date, { weekStartsOn: 1 }),
      };
    case 'work_week':
      const weekStart = startOfWeek(date, { weekStartsOn: 1 });
      return {
        start: weekStart,
        end: addHours(weekStart, 120), // Monday to Friday
      };
    case 'day':
      return {
        start: startOfDay(date),
        end: endOfDay(date),
      };
    case 'agenda':
      return {
        start: date,
        end: addHours(date, 24 * 30), // Next 30 days
      };
    default:
      return {
        start: startOfWeek(date, { weekStartsOn: 1 }),
        end: endOfWeek(date, { weekStartsOn: 1 }),
      };
  }
}

/**
 * Format calendar event time for display
 */
export function formatEventTime(event: CalendarEvent): string {
  if (event.allDay) {
    return 'All day';
  }

  const startTime = format(event.start, 'HH:mm');
  const endTime = format(event.end, 'HH:mm');

  return `${startTime} - ${endTime}`;
}

/**
 * Get calendar event duration in hours
 */
export function getEventDurationHours(event: CalendarEvent): number {
  const diffMs = event.end.getTime() - event.start.getTime();
  return diffMs / (1000 * 60 * 60); // Convert ms to hours
}

/**
 * Create a new task from calendar slot info
 */
export function createTaskFromSlot(slotInfo: {
  start: Date;
  end: Date;
  action: string;
}): Partial<Task> {
  const isAllDay =
    slotInfo.action === 'select' &&
    slotInfo.end.getTime() - slotInfo.start.getTime() >= 24 * 60 * 60 * 1000;

  return {
    title: '',
    description: '',
    status: 'todo' as const,
    priority: 'medium' as const,
    start_date: isAllDay ? undefined : slotInfo.start.toISOString(),
    due_date: slotInfo.end.toISOString(),
    estimated_hours: isAllDay
      ? undefined
      : getEventDurationHours({
          start: slotInfo.start,
          end: slotInfo.end,
        } as CalendarEvent),
  };
}

/**
 * Check if event overlaps with date range
 */
export function isEventInRange(event: CalendarEvent, start: Date, end: Date): boolean {
  return event.end >= start && event.start <= end;
}

/**
 * Get default calendar views configuration
 */
export const CALENDAR_VIEWS = {
  month: true,
  week: true,
  work_week: true,
  day: true,
  agenda: true,
} as const;

/**
 * Calendar toolbar messages/labels
 */
export const CALENDAR_MESSAGES = {
  allDay: 'All Day',
  previous: 'Previous',
  next: 'Next',
  today: 'Today',
  month: 'Month',
  week: 'Week',
  work_week: 'Work Week',
  day: 'Day',
  agenda: 'Agenda',
  date: 'Date',
  time: 'Time',
  event: 'Event',
  noEventsInRange: 'No tasks in this date range',
  showMore: (total: number) => `+${total} more`,
} as const;
