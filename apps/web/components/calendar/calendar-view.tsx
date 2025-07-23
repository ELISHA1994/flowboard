'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { Calendar, dateFnsLocalizer, View, SlotInfo } from 'react-big-calendar';
import {
  format,
  parse,
  startOfWeek,
  getDay,
  addMonths,
  subMonths,
  addWeeks,
  subWeeks,
  addDays,
  subDays,
} from 'date-fns';
import { enUS } from 'date-fns/locale';

// Import calendar styles
import 'react-big-calendar/lib/css/react-big-calendar.css';

// Local imports
import { CalendarEvent, CALENDAR_VIEWS, CALENDAR_MESSAGES } from '@/lib/calendar/calendar-utils';
import {
  useCalendarTasks,
  useCalendarOperations,
  CalendarFilters,
} from '@/hooks/use-calendar-tasks';
import { CalendarToolbar } from './calendar-toolbar';
import { CalendarEventComponent } from './calendar-event';
import { CalendarFiltersPanel } from './calendar-filters';
import { TaskCreationModal } from './task-creation-modal';
import { TaskDetailModal } from './task-detail-modal';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight, Plus } from 'lucide-react';

// Setup date-fns localizer
const locales = {
  'en-US': enUS,
};

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales,
});

interface CalendarViewProps {
  className?: string;
  defaultView?: View;
  defaultDate?: Date;
  height?: number | string;
  showFilters?: boolean;
  onSelectEvent?: (event: CalendarEvent) => void;
  onSelectSlot?: (slotInfo: SlotInfo) => void;
  onNavigate?: (date: Date) => void;
}

export function CalendarView({
  className,
  defaultView = 'month',
  defaultDate = new Date(),
  height = 600,
  showFilters = true,
  onSelectEvent,
  onSelectSlot,
  onNavigate,
}: CalendarViewProps) {
  // State management
  const [currentDate, setCurrentDate] = useState(defaultDate);
  const [currentView, setCurrentView] = useState<View>(defaultView);
  const [filters, setFilters] = useState<CalendarFilters>({
    show_completed: true,
  });
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [newTaskSlot, setNewTaskSlot] = useState<SlotInfo | null>(null);

  // Data fetching
  const {
    data: events = [],
    isLoading,
    error,
  } = useCalendarTasks(currentDate, currentView, filters);

  // Operations
  const { updateDates, updateStatus } = useCalendarOperations();

  // Event handlers
  const handleNavigate = useCallback(
    (newDate: Date) => {
      setCurrentDate(newDate);
      onNavigate?.(newDate);
    },
    [onNavigate]
  );

  const handleViewChange = useCallback((newView: View) => {
    setCurrentView(newView);
  }, []);

  const handleSelectEvent = useCallback(
    (event: CalendarEvent) => {
      setSelectedEvent(event);
      if (onSelectEvent) {
        onSelectEvent(event);
      } else {
        setShowDetailModal(true);
      }
    },
    [onSelectEvent]
  );

  const handleSelectSlot = useCallback(
    (slotInfo: SlotInfo) => {
      setNewTaskSlot(slotInfo);
      if (onSelectSlot) {
        onSelectSlot(slotInfo);
      } else {
        setShowCreateModal(true);
      }
    },
    [onSelectSlot]
  );

  const handleEventDrop = useCallback(
    ({
      event,
      start,
      end,
      allDay,
    }: {
      event: CalendarEvent;
      start: Date;
      end: Date;
      allDay?: boolean;
    }) => {
      updateDates.mutate({
        taskId: event.id,
        start,
        end,
        allDay: allDay || false,
      });
    },
    [updateDates]
  );

  const handleEventResize = useCallback(
    ({ event, start, end }: { event: CalendarEvent; start: Date; end: Date }) => {
      updateDates.mutate({
        taskId: event.id,
        start,
        end,
        allDay: event.allDay,
      });
    },
    [updateDates]
  );

  // Navigation helpers
  const navigateToDate = useCallback(
    (direction: 'prev' | 'next' | 'today') => {
      let newDate = currentDate;

      switch (direction) {
        case 'prev':
          if (currentView === 'month') newDate = subMonths(currentDate, 1);
          else if (currentView === 'week' || currentView === 'work_week')
            newDate = subWeeks(currentDate, 1);
          else if (currentView === 'day') newDate = subDays(currentDate, 1);
          break;
        case 'next':
          if (currentView === 'month') newDate = addMonths(currentDate, 1);
          else if (currentView === 'week' || currentView === 'work_week')
            newDate = addWeeks(currentDate, 1);
          else if (currentView === 'day') newDate = addDays(currentDate, 1);
          break;
        case 'today':
          newDate = new Date();
          break;
      }

      setCurrentDate(newDate);
    },
    [currentDate, currentView]
  );

  // Custom event styling
  const eventStyleGetter = useCallback((event: CalendarEvent) => {
    return {
      style: {
        backgroundColor: event.backgroundColor,
        borderColor: event.borderColor,
        color: event.textColor,
        border: `2px solid ${event.borderColor}`,
        borderRadius: '4px',
        opacity: event.resource.status === 'done' ? 0.7 : 1,
        fontSize: '12px',
        padding: '2px 4px',
      },
    };
  }, []);

  // Custom day prop getter for styling
  const dayPropGetter = useCallback((date: Date) => {
    const isToday = format(date, 'yyyy-MM-dd') === format(new Date(), 'yyyy-MM-dd');
    return {
      className: isToday ? 'rbc-today-highlight' : '',
    };
  }, []);

  // Memoized calendar component
  const calendarComponent = useMemo(
    () => (
      <Calendar
        localizer={localizer}
        events={events}
        startAccessor="start"
        endAccessor="end"
        titleAccessor="title"
        allDayAccessor="allDay"
        resourceAccessor="resource"
        views={CALENDAR_VIEWS}
        view={currentView}
        date={currentDate}
        onNavigate={handleNavigate}
        onView={handleViewChange}
        onSelectEvent={handleSelectEvent}
        onSelectSlot={handleSelectSlot}
        onEventDrop={handleEventDrop}
        onEventResize={handleEventResize}
        selectable={true}
        resizable={true}
        dragFromOutsideItem={null}
        eventPropGetter={eventStyleGetter}
        dayPropGetter={dayPropGetter}
        messages={CALENDAR_MESSAGES}
        popup={true}
        popupOffset={30}
        step={30}
        timeslots={2}
        components={{
          event: CalendarEventComponent,
          toolbar: (props) => (
            <CalendarToolbar
              {...props}
              onNavigate={navigateToDate}
              isLoading={isLoading}
              onCreateTask={() => setShowCreateModal(true)}
            />
          ),
        }}
        formats={{
          dayFormat: 'EEE dd',
          dayHeaderFormat: 'EEEE, MMMM do',
          dayRangeHeaderFormat: ({ start, end }) =>
            `${format(start, 'MMM d')} - ${format(end, 'MMM d, yyyy')}`,
          monthHeaderFormat: 'MMMM yyyy',
          agendaHeaderFormat: ({ start, end }) =>
            `${format(start, 'MMM d')} - ${format(end, 'MMM d, yyyy')}`,
          agendaDateFormat: 'EEE MMM dd',
          agendaTimeFormat: 'h:mm a',
          agendaTimeRangeFormat: ({ start, end }) =>
            `${format(start, 'h:mm a')} - ${format(end, 'h:mm a')}`,
        }}
      />
    ),
    [
      events,
      currentView,
      currentDate,
      handleNavigate,
      handleViewChange,
      handleSelectEvent,
      handleSelectSlot,
      handleEventDrop,
      handleEventResize,
      eventStyleGetter,
      dayPropGetter,
      navigateToDate,
      isLoading,
    ]
  );

  return (
    <div className={cn('calendar-container', className)}>
      {/* Filters Panel */}
      {showFilters && (
        <CalendarFiltersPanel filters={filters} onFiltersChange={setFilters} className="mb-4" />
      )}

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-600 text-sm">Failed to load calendar events: {error.message}</p>
        </div>
      )}

      {/* Calendar Container */}
      <div
        className="calendar-wrapper bg-card border rounded-lg overflow-hidden shadow-sm"
        style={{ height }}
      >
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : (
          calendarComponent
        )}
      </div>

      {/* Task Creation Modal */}
      <TaskCreationModal
        open={showCreateModal}
        onOpenChange={setShowCreateModal}
        slotInfo={newTaskSlot}
        onSuccess={() => {
          setShowCreateModal(false);
          setNewTaskSlot(null);
        }}
      />

      {/* Task Detail Modal */}
      <TaskDetailModal
        open={showDetailModal}
        onOpenChange={setShowDetailModal}
        event={selectedEvent}
        onSuccess={() => {
          setShowDetailModal(false);
          setSelectedEvent(null);
        }}
      />
    </div>
  );
}

// Default export
export default CalendarView;
