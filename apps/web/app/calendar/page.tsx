'use client';

import React from 'react';
import { DashboardLayout } from '@/components/layouts/dashboard-layout';
import { EnhancedCalendarView } from '@/components/calendar/enhanced-calendar-view';

// Import calendar styles
import '@/styles/calendar.css';

export default function CalendarPage() {
  return (
    <DashboardLayout>
      <div className="flex-1 space-y-6 p-8 pt-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Calendar</h2>
            <p className="text-muted-foreground">View and manage your tasks in a calendar format</p>
          </div>
        </div>

        {/* Enhanced Calendar Component with Time Tracking */}
        <EnhancedCalendarView />
      </div>
    </DashboardLayout>
  );
}
