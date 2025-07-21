'use client';

import { useState } from 'react';
import { DashboardLayout } from '@/components/layouts/dashboard-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import {
  Activity,
  CheckCircle2,
  Circle,
  Clock,
  Plus,
  Users,
  Calendar,
  AlertCircle,
} from 'lucide-react';
import { useTaskStatistics, useRecentTasks, useUpcomingTasks } from '@/hooks/use-tasks';
import { useRecentActivity } from '@/hooks/use-notifications';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { format, formatDistanceToNow, isToday, isTomorrow, parseISO } from 'date-fns';
import { CreateTaskModal } from '@/components/tasks/create-task-modal';
import { EditTaskModal } from '@/components/tasks/edit-task-modal';
import { Task } from '@/lib/api/tasks';

export default function DashboardPage() {
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const { statistics, loading: statsLoading, error: statsError } = useTaskStatistics();
  const {
    tasks: recentTasks,
    loading: recentLoading,
    error: recentError,
    refetch: refetchRecent,
  } = useRecentTasks(5);
  const {
    tasks: upcomingTasks,
    loading: upcomingLoading,
    error: upcomingError,
    refetch: refetchUpcoming,
  } = useUpcomingTasks(7);
  const {
    activities,
    loading: activityLoading,
    error: activityError,
    refetch: refetchActivity,
  } = useRecentActivity(5);

  // Show a general error if all requests fail
  const hasErrors = statsError || recentError || upcomingError || activityError;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Global Error Alert */}
        {hasErrors && !statistics && !recentTasks.length && !upcomingTasks.length && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Unable to load dashboard data. Please check your connection and try refreshing the
              page.
            </AlertDescription>
          </Alert>
        )}

        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
            <p className="text-muted-foreground">
              Welcome back! Here&apos;s what&apos;s happening with your tasks today.
            </p>
          </div>
          <Button onClick={() => setCreateModalOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New Task
          </Button>
        </div>

        {/* Stats Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Tasks</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {statsLoading ? (
                <div>
                  <Skeleton className="h-8 w-16 mb-1" />
                  <Skeleton className="h-4 w-24" />
                </div>
              ) : (
                <>
                  <div className="text-2xl font-bold">{statistics?.total_tasks || 0}</div>
                  <p className="text-xs text-muted-foreground">
                    {statistics?.completion_rate
                      ? `${statistics.completion_rate.toFixed(1)}% completion rate`
                      : 'No data'}
                  </p>
                </>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">In Progress</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {statsLoading ? (
                <div>
                  <Skeleton className="h-8 w-16 mb-1" />
                  <Skeleton className="h-4 w-24" />
                </div>
              ) : (
                <>
                  <div className="text-2xl font-bold">
                    {statistics?.tasks_by_status?.in_progress || 0}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {statistics?.overdue_tasks
                      ? `${statistics.overdue_tasks} overdue`
                      : 'No overdue tasks'}
                  </p>
                </>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completed</CardTitle>
              <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {statsLoading ? (
                <div>
                  <Skeleton className="h-8 w-16 mb-1" />
                  <Skeleton className="h-4 w-24" />
                </div>
              ) : (
                <>
                  <div className="text-2xl font-bold">{statistics?.tasks_by_status?.done || 0}</div>
                  <p className="text-xs text-muted-foreground">
                    {statistics?.average_completion_time
                      ? `~${Math.round(statistics.average_completion_time)} days avg`
                      : 'Track your progress'}
                  </p>
                </>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">To Do</CardTitle>
              <Circle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {statsLoading ? (
                <div>
                  <Skeleton className="h-8 w-16 mb-1" />
                  <Skeleton className="h-4 w-24" />
                </div>
              ) : (
                <>
                  <div className="text-2xl font-bold">{statistics?.tasks_by_status?.todo || 0}</div>
                  <p className="text-xs text-muted-foreground">
                    {statistics?.tasks_by_priority?.urgent
                      ? `${statistics.tasks_by_priority.urgent} urgent`
                      : 'Ready to start'}
                  </p>
                </>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Main Content Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
          {/* Recent Tasks */}
          <Card className="lg:col-span-4">
            <CardHeader>
              <CardTitle>Recent Tasks</CardTitle>
              <CardDescription>Your most recently updated tasks</CardDescription>
            </CardHeader>
            <CardContent>
              {recentError ? (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{recentError}</AlertDescription>
                </Alert>
              ) : recentLoading ? (
                <div className="space-y-4">
                  {[...Array(5)].map((_, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between rounded-lg border p-4"
                    >
                      <div className="flex items-center space-x-4">
                        <Skeleton className="h-5 w-5 rounded-full" />
                        <div>
                          <Skeleton className="h-4 w-48 mb-2" />
                          <Skeleton className="h-3 w-32" />
                        </div>
                      </div>
                      <Skeleton className="h-8 w-8 rounded-full" />
                    </div>
                  ))}
                </div>
              ) : recentTasks.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Circle className="h-12 w-12 mx-auto mb-4 opacity-20" />
                  <p>No tasks yet. Create your first task to get started!</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {recentTasks.map((task) => (
                    <div
                      key={task.id}
                      className="flex items-center justify-between rounded-lg border p-4 hover:bg-muted/50 transition-colors cursor-pointer"
                      onClick={() => {
                        setSelectedTask(task);
                        setEditModalOpen(true);
                      }}
                    >
                      <div className="flex items-center space-x-4">
                        <div>
                          {task.status === 'done' ? (
                            <CheckCircle2 className="h-5 w-5 text-green-600" />
                          ) : task.status === 'in_progress' ? (
                            <Clock className="h-5 w-5 text-blue-600" />
                          ) : (
                            <Circle className="h-5 w-5 text-muted-foreground" />
                          )}
                        </div>
                        <div>
                          <p className="font-medium">{task.title}</p>
                          <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                            <span
                              className={cn(
                                'rounded-full px-2 py-0.5 text-xs font-medium',
                                task.priority === 'urgent' &&
                                  'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400',
                                task.priority === 'high' &&
                                  'bg-orange-100 text-orange-700 dark:bg-orange-900/20 dark:text-orange-400',
                                task.priority === 'medium' &&
                                  'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400',
                                task.priority === 'low' &&
                                  'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400'
                              )}
                            >
                              {task.priority}
                            </span>
                            <span>•</span>
                            <span>
                              {task.due_date
                                ? isToday(parseISO(task.due_date))
                                  ? 'Today'
                                  : isTomorrow(parseISO(task.due_date))
                                    ? 'Tomorrow'
                                    : format(parseISO(task.due_date), 'MMM d')
                                : 'No due date'}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {task.assigned_to && (
                          <div
                            className="flex h-8 w-8 items-center justify-center rounded-full bg-muted text-xs font-medium"
                            title={task.assigned_to.username}
                          >
                            {task.assigned_to.username.substring(0, 2).toUpperCase()}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Activity Feed */}
          <Card className="lg:col-span-3">
            <CardHeader>
              <CardTitle>Activity</CardTitle>
              <CardDescription>Recent activity in your workspace</CardDescription>
            </CardHeader>
            <CardContent>
              {activityError ? (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{activityError}</AlertDescription>
                </Alert>
              ) : activityLoading ? (
                <div className="space-y-4">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="flex items-start space-x-3">
                      <Skeleton className="h-8 w-8 rounded-full" />
                      <div className="flex-1 space-y-2">
                        <Skeleton className="h-4 w-48" />
                        <Skeleton className="h-3 w-24" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : activities.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Activity className="h-12 w-12 mx-auto mb-4 opacity-20" />
                  <p>No recent activity to show</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {activities.map((activity) => (
                    <div key={activity.id} className="flex items-start space-x-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted text-xs font-medium">
                        {activity.user_initials}
                      </div>
                      <div className="flex-1 space-y-1">
                        <p className="text-sm">
                          <span className="font-medium">{activity.user}</span> {activity.action}{' '}
                          {activity.task && <span className="font-medium">{activity.task}</span>}
                          {activity.project && (
                            <span className="font-medium">{activity.project}</span>
                          )}
                        </p>
                        <p className="text-xs text-muted-foreground">{activity.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Upcoming Deadlines */}
        <Card>
          <CardHeader>
            <CardTitle>Upcoming Deadlines</CardTitle>
            <CardDescription>Tasks due in the next 7 days</CardDescription>
          </CardHeader>
          <CardContent>
            {upcomingError ? (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{upcomingError}</AlertDescription>
              </Alert>
            ) : upcomingLoading ? (
              <div className="space-y-4">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="flex space-x-4">
                    <Skeleton className="w-24 h-4" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-48" />
                      <Skeleton className="h-4 w-36" />
                    </div>
                  </div>
                ))}
              </div>
            ) : upcomingTasks.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Calendar className="h-12 w-12 mx-auto mb-4 opacity-20" />
                <p>No upcoming deadlines in the next 7 days</p>
              </div>
            ) : (
              <div className="space-y-4">
                {(() => {
                  // Group tasks by date
                  const tasksByDate = upcomingTasks.reduce(
                    (acc, task) => {
                      if (!task.due_date) return acc;

                      const date = parseISO(task.due_date);
                      let dateLabel: string;

                      if (isToday(date)) {
                        dateLabel = 'Today';
                      } else if (isTomorrow(date)) {
                        dateLabel = 'Tomorrow';
                      } else {
                        dateLabel = format(date, 'EEEE');
                      }

                      if (!acc[dateLabel]) {
                        acc[dateLabel] = [];
                      }
                      acc[dateLabel].push(task);
                      return acc;
                    },
                    {} as Record<string, typeof upcomingTasks>
                  );

                  return Object.entries(tasksByDate).map(([date, tasks]) => (
                    <div key={date} className="flex space-x-4">
                      <div className="w-24 text-sm font-medium text-muted-foreground">{date}</div>
                      <div className="flex-1 space-y-2">
                        {tasks.map((task) => (
                          <div key={task.id} className="flex items-center space-x-2 text-sm">
                            <Calendar className="h-4 w-4 text-muted-foreground" />
                            <span className="flex-1">{task.title}</span>
                            <span
                              className={cn(
                                'text-xs px-1.5 py-0.5 rounded',
                                task.priority === 'urgent' &&
                                  'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400',
                                task.priority === 'high' &&
                                  'bg-orange-100 text-orange-700 dark:bg-orange-900/20 dark:text-orange-400',
                                task.priority === 'medium' &&
                                  'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400',
                                task.priority === 'low' &&
                                  'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400'
                              )}
                            >
                              {task.priority}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ));
                })()}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Create Task Modal */}
      <CreateTaskModal
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
        onTaskCreated={() => {
          refetchRecent();
          refetchUpcoming();
        }}
      />

      {/* Edit Task Modal */}
      <EditTaskModal
        open={editModalOpen}
        onOpenChange={setEditModalOpen}
        task={selectedTask}
        onTaskUpdated={() => {
          refetchRecent();
          refetchUpcoming();
          setSelectedTask(null);
        }}
      />
    </DashboardLayout>
  );
}
