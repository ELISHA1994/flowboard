'use client';

import React from 'react';
import { EventProps } from 'react-big-calendar';
import { CalendarEvent } from '@/lib/calendar/calendar-utils';
import { Clock, AlertTriangle, CheckCircle2, Circle, Pause, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

// Status icon mapping
const statusIcons = {
  todo: Circle,
  in_progress: Clock,
  done: CheckCircle2,
  cancelled: X,
};

// Priority indicators with enhanced colors
const priorityIndicators = {
  urgent: { color: 'text-red-500', bgColor: 'bg-red-500/20', icon: AlertTriangle },
  high: { color: 'text-orange-500', bgColor: 'bg-orange-500/20', icon: AlertTriangle },
  medium: { color: 'text-blue-500', bgColor: 'bg-blue-500/20', icon: Circle },
  low: { color: 'text-green-500', bgColor: 'bg-green-500/20', icon: Circle },
};

interface CalendarEventComponentProps extends EventProps<CalendarEvent> {
  className?: string;
}

export function CalendarEventComponent({ event, className }: CalendarEventComponentProps) {
  const task = event.resource;
  const StatusIcon = statusIcons[task.status];
  const priorityInfo = priorityIndicators[task.priority];
  const PriorityIcon = priorityInfo.icon;

  return (
    <div
      className={cn(
        'calendar-event h-full w-full flex items-center gap-1.5 px-2 py-1 text-xs font-medium overflow-hidden transition-all',
        'hover:shadow-md hover:scale-[1.02]',
        task.status === 'done' && 'opacity-75',
        className
      )}
      style={{
        background: `linear-gradient(135deg, ${event.backgroundColor}dd, ${event.backgroundColor}99)`,
        color: event.textColor,
        border: `1px solid ${event.borderColor}`,
        borderRadius: '6px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      }}
    >
      {/* Status Icon */}
      <StatusIcon className="h-3 w-3 flex-shrink-0" strokeWidth={2.5} />

      {/* Task Title */}
      <span className="flex-1 truncate font-semibold leading-tight">{event.title}</span>

      {/* Priority Indicator */}
      {(task.priority === 'urgent' || task.priority === 'high') && (
        <div className={cn('rounded-full p-0.5', priorityInfo.bgColor)}>
          <PriorityIcon className={cn('h-2.5 w-2.5', priorityInfo.color)} strokeWidth={2.5} />
        </div>
      )}

      {/* Project Badge (for larger events) */}
      {event.project && (
        <Badge
          variant="secondary"
          className="hidden sm:inline-flex h-4 px-1 text-xs bg-white/20 text-inherit border-none"
        >
          {event.project}
        </Badge>
      )}
    </div>
  );
}

// Month view event component (simplified for smaller space)
export function MonthEventComponent({ event }: EventProps<CalendarEvent>) {
  const task = event.resource;
  const StatusIcon = statusIcons[task.status];

  return (
    <div
      className="calendar-event-month flex items-center gap-1 px-1.5 py-1 text-xs truncate transition-all hover:scale-[1.02] hover:shadow-sm"
      style={{
        background: `linear-gradient(to right, ${event.borderColor}20, ${event.backgroundColor}99)`,
        color: event.textColor,
        borderLeft: `3px solid ${event.borderColor}`,
        borderRadius: '4px',
      }}
    >
      <StatusIcon className="h-2.5 w-2.5 flex-shrink-0" strokeWidth={2.5} />
      <span className="truncate flex-1 font-medium">{event.title}</span>
      {task.priority === 'urgent' && (
        <AlertTriangle className="h-2.5 w-2.5 text-red-500" strokeWidth={2.5} />
      )}
    </div>
  );
}

// Agenda view event component (more detailed)
export function AgendaEventComponent({ event }: EventProps<CalendarEvent>) {
  const task = event.resource;
  const StatusIcon = statusIcons[task.status];
  const priorityInfo = priorityIndicators[task.priority];

  return (
    <div className="calendar-event-agenda flex items-center gap-3 p-2 text-sm">
      {/* Status and Priority */}
      <div className="flex items-center gap-2">
        <StatusIcon className="h-4 w-4" style={{ color: event.textColor }} />
        <Badge
          variant="outline"
          className={cn('text-xs border-0', priorityInfo.color, priorityInfo.bgColor)}
        >
          {task.priority}
        </Badge>
      </div>

      {/* Event Content */}
      <div className="flex-1 min-w-0">
        <div className="font-medium truncate">{event.title}</div>
        {task.description && (
          <div className="text-xs text-muted-foreground mt-1 line-clamp-2">{task.description}</div>
        )}
      </div>

      {/* Project and Time */}
      <div className="flex flex-col items-end gap-1 text-xs text-muted-foreground">
        {event.project && (
          <Badge variant="secondary" className="text-xs">
            {event.project}
          </Badge>
        )}
        {!event.allDay && (
          <div className="font-mono">
            {new Date(event.start).toLocaleTimeString('en-US', {
              hour: 'numeric',
              minute: '2-digit',
              hour12: true,
            })}
          </div>
        )}
      </div>
    </div>
  );
}

// Event tooltip component
export function EventTooltip({ event }: { event: CalendarEvent }) {
  const task = event.resource;

  return (
    <div className="calendar-event-tooltip bg-popover text-popover-foreground border rounded-lg shadow-lg p-3 text-sm max-w-xs">
      <div className="font-semibold mb-2">{event.title}</div>

      {task.description && (
        <div className="text-muted-foreground mb-2 line-clamp-3">{task.description}</div>
      )}

      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">Status:</span>
          <Badge variant="outline">{task.status.replace('_', ' ')}</Badge>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">Priority:</span>
          <Badge variant="outline">{task.priority}</Badge>
        </div>

        {event.project && (
          <div className="flex items-center gap-2">
            <span className="text-muted-foreground">Project:</span>
            <Badge variant="secondary">{event.project}</Badge>
          </div>
        )}

        {task.estimated_hours && (
          <div className="flex items-center gap-2">
            <Clock className="h-3 w-3 text-muted-foreground" />
            <span className="text-muted-foreground">{task.estimated_hours}h estimated</span>
          </div>
        )}

        {!event.allDay && (
          <div className="text-muted-foreground text-xs mt-2">
            {new Date(event.start).toLocaleString()} - {new Date(event.end).toLocaleString()}
          </div>
        )}
      </div>
    </div>
  );
}

// Default export
export default CalendarEventComponent;
