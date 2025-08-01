'use client';

import React, { useState, useMemo } from 'react';
import { CalendarView } from './calendar-view';
import { TimeTrackingHeatmap, WeeklyTimeDistribution } from './time-tracking-heatmap';
import { TeamPerformanceChart } from './team-performance-chart';
import { useCalendarTasks } from '@/hooks/use-calendar-tasks';
import { useAuth } from '@/contexts/auth-context';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Calendar, Clock, BarChart3 } from 'lucide-react';
import { startOfMonth, endOfMonth } from 'date-fns';
import { cn } from '@/lib/utils';

export function EnhancedCalendarView() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [activeTab, setActiveTab] = useState('calendar');
  const { user } = useAuth();

  // Fetch tasks for the current month
  const { data: events, isLoading } = useCalendarTasks(
    currentDate,
    'month',
    { show_completed: true } // Include completed tasks for time tracking
  );

  // Extract tasks from calendar events
  const tasks = events?.map((event) => event.resource) || [];

  // Extract real team members from tasks
  const teamMembers = useMemo(() => {
    const uniqueAssignees = new Map();

    // Add current user if they have tasks
    if (user) {
      const userHasTasks = tasks.some(
        (task) => task.user_id === user.id || task.assigned_to_id === user.id
      );
      if (userHasTasks) {
        uniqueAssignees.set(user.id, {
          id: user.id,
          name: user.name || user.username || 'Current User',
          email: user.email,
          avatar: undefined,
        });
      }
    }

    // Extract unique assignees from tasks who have actual assignments
    tasks.forEach((task) => {
      if (task.assigned_to_id && !uniqueAssignees.has(task.assigned_to_id)) {
        // Check if we have assignee details from the task
        if (task.assigned_to) {
          uniqueAssignees.set(task.assigned_to_id, {
            id: task.assigned_to_id,
            name: task.assigned_to.full_name || task.assigned_to.username || 'Unknown User',
            email: task.assigned_to.email,
            avatar: undefined,
          });
        } else {
          // Fallback if assignee details not populated
          uniqueAssignees.set(task.assigned_to_id, {
            id: task.assigned_to_id,
            name: `User ${task.assigned_to_id.slice(0, 8)}`,
            email: `user${task.assigned_to_id.slice(0, 8)}@example.com`,
            avatar: undefined,
          });
        }
      }

      // Also include task owners (user_id) if different from assigned_to
      if (task.user_id && !uniqueAssignees.has(task.user_id)) {
        uniqueAssignees.set(task.user_id, {
          id: task.user_id,
          name: `User ${task.user_id.slice(0, 8)}`,
          email: `user${task.user_id.slice(0, 8)}@example.com`,
          avatar: undefined,
        });
      }
    });

    return Array.from(uniqueAssignees.values());
  }, [tasks, user]);

  return (
    <div className="space-y-6">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid grid-cols-3 w-full max-w-md">
          <TabsTrigger value="calendar" className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            Calendar
          </TabsTrigger>
          <TabsTrigger value="heatmap" className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Time Tracking
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Analytics
          </TabsTrigger>
        </TabsList>

        <TabsContent value="calendar" className="mt-6">
          <CalendarView
            height="calc(100vh - 320px)"
            showFilters={true}
            defaultDate={currentDate}
            onNavigate={(date) => setCurrentDate(date)}
          />
        </TabsContent>

        <TabsContent value="heatmap" className="mt-6">
          <div className="grid gap-6 md:grid-cols-2">
            <TimeTrackingHeatmap tasks={tasks} month={currentDate} className="md:col-span-2" />
            <WeeklyTimeDistribution tasks={tasks} className="md:col-span-2 lg:col-span-1" />

            {/* Monthly Progress */}
            <div className="bg-card border rounded-lg p-6 md:col-span-2 lg:col-span-1">
              <h3 className="text-lg font-semibold mb-4">Time Tracking Tips</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>• Track actual hours spent on each task for accurate insights</li>
                <li>• Set estimated hours to compare with actual time spent</li>
                <li>• Review your heatmap weekly to identify productivity patterns</li>
                <li>• Focus on consistency rather than long hours</li>
              </ul>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="mt-6">
          <div className="grid gap-6 md:grid-cols-2">
            <TeamPerformanceChart
              tasks={tasks}
              teamMembers={teamMembers}
              className="md:col-span-2"
            />

            {/* Additional Analytics Cards */}
            <div className="bg-card border rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Project Distribution</h3>
              <div className="space-y-3">
                {(() => {
                  const projectCounts = tasks.reduce(
                    (acc, task) => {
                      const projectName = task.project?.name || 'No Project';
                      acc[projectName] = (acc[projectName] || 0) + 1;
                      return acc;
                    },
                    {} as Record<string, number>
                  );

                  const total = Object.values(projectCounts).reduce((sum, count) => sum + count, 0);

                  return Object.entries(projectCounts).map(([project, count]) => (
                    <div key={project}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-muted-foreground">{project}</span>
                        <span className="font-medium">
                          {count} ({Math.round((count / total) * 100)}%)
                        </span>
                      </div>
                      <div className="w-full bg-secondary rounded-full h-2">
                        <div
                          className="bg-primary h-2 rounded-full transition-all"
                          style={{ width: `${(count / total) * 100}%` }}
                        />
                      </div>
                    </div>
                  ));
                })()}
              </div>
            </div>

            <div className="bg-card border rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-4">Priority Breakdown</h3>
              <div className="space-y-3">
                {(() => {
                  const priorityCounts = tasks.reduce(
                    (acc, task) => {
                      acc[task.priority] = (acc[task.priority] || 0) + 1;
                      return acc;
                    },
                    {} as Record<string, number>
                  );

                  const priorities = ['urgent', 'high', 'medium', 'low'];
                  const colors = {
                    urgent: 'bg-red-500',
                    high: 'bg-orange-500',
                    medium: 'bg-yellow-500',
                    low: 'bg-green-500',
                  };

                  return priorities.map((priority) => {
                    const count = priorityCounts[priority] || 0;
                    const total = tasks.length || 1;

                    return (
                      <div key={priority}>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-muted-foreground capitalize">{priority}</span>
                          <span className="font-medium">{count}</span>
                        </div>
                        <div className="w-full bg-secondary rounded-full h-2">
                          <div
                            className={cn(
                              'h-2 rounded-full transition-all',
                              colors[priority as keyof typeof colors]
                            )}
                            style={{ width: `${(count / total) * 100}%` }}
                          />
                        </div>
                      </div>
                    );
                  });
                })()}
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default EnhancedCalendarView;
