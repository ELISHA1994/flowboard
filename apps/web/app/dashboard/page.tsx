import { DashboardLayout } from '@/components/layouts/dashboard-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Activity, CheckCircle2, Circle, Clock, Plus, Users, Calendar } from 'lucide-react';

export default function DashboardPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
            <p className="text-muted-foreground">
              Welcome back! Here&apos;s what&apos;s happening with your tasks today.
            </p>
          </div>
          <Button>
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
              <div className="text-2xl font-bold">254</div>
              <p className="text-xs text-muted-foreground">+20.1% from last month</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">In Progress</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">12</div>
              <p className="text-xs text-muted-foreground">3 due today</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completed</CardTitle>
              <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">89</div>
              <p className="text-xs text-muted-foreground">+12% completion rate</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Team Members</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">8</div>
              <p className="text-xs text-muted-foreground">2 new this week</p>
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
              <div className="space-y-4">
                {[
                  {
                    title: 'Update user dashboard UI',
                    status: 'in-progress',
                    priority: 'high',
                    assignee: 'JD',
                    due: 'Today',
                  },
                  {
                    title: 'Fix authentication bug',
                    status: 'todo',
                    priority: 'urgent',
                    assignee: 'ME',
                    due: 'Tomorrow',
                  },
                  {
                    title: 'Write API documentation',
                    status: 'completed',
                    priority: 'medium',
                    assignee: 'AS',
                    due: 'Completed',
                  },
                  {
                    title: 'Review pull requests',
                    status: 'in-progress',
                    priority: 'medium',
                    assignee: 'JD',
                    due: 'Today',
                  },
                  {
                    title: 'Deploy to production',
                    status: 'todo',
                    priority: 'high',
                    assignee: 'ME',
                    due: 'This week',
                  },
                ].map((task, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between rounded-lg border p-4"
                  >
                    <div className="flex items-center space-x-4">
                      <div>
                        {task.status === 'completed' ? (
                          <CheckCircle2 className="h-5 w-5 text-green-600" />
                        ) : task.status === 'in-progress' ? (
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
                              task.priority === 'urgent' && 'bg-red-100 text-red-700',
                              task.priority === 'high' && 'bg-orange-100 text-orange-700',
                              task.priority === 'medium' && 'bg-yellow-100 text-yellow-700',
                              task.priority === 'low' && 'bg-green-100 text-green-700'
                            )}
                          >
                            {task.priority}
                          </span>
                          <span>•</span>
                          <span>{task.due}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted text-xs font-medium">
                        {task.assignee}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Activity Feed */}
          <Card className="lg:col-span-3">
            <CardHeader>
              <CardTitle>Activity</CardTitle>
              <CardDescription>Recent activity in your workspace</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  {
                    user: 'John Doe',
                    action: 'completed',
                    task: 'Update user dashboard UI',
                    time: '2 hours ago',
                  },
                  {
                    user: 'Sarah Smith',
                    action: 'commented on',
                    task: 'Fix authentication bug',
                    time: '3 hours ago',
                  },
                  {
                    user: 'Mike Johnson',
                    action: 'assigned',
                    task: 'Write API documentation',
                    time: '5 hours ago',
                  },
                  {
                    user: 'Emily Brown',
                    action: 'created',
                    task: 'Deploy to production',
                    time: '1 day ago',
                  },
                  {
                    user: 'You',
                    action: 'updated',
                    task: 'Review pull requests',
                    time: '2 days ago',
                  },
                ].map((activity, index) => (
                  <div key={index} className="flex items-start space-x-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted text-xs font-medium">
                      {activity.user
                        .split(' ')
                        .map((n) => n[0])
                        .join('')}
                    </div>
                    <div className="flex-1 space-y-1">
                      <p className="text-sm">
                        <span className="font-medium">{activity.user}</span> {activity.action}{' '}
                        <span className="font-medium">{activity.task}</span>
                      </p>
                      <p className="text-xs text-muted-foreground">{activity.time}</p>
                    </div>
                  </div>
                ))}
              </div>
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
            <div className="space-y-4">
              {[
                { date: 'Today', tasks: ['Update user dashboard UI', 'Review pull requests'] },
                { date: 'Tomorrow', tasks: ['Fix authentication bug', 'Team standup meeting'] },
                { date: 'Friday', tasks: ['Deploy to production', 'Weekly report'] },
                { date: 'Next Monday', tasks: ['Client presentation', 'Sprint planning'] },
              ].map((day, index) => (
                <div key={index} className="flex space-x-4">
                  <div className="w-24 text-sm font-medium text-muted-foreground">{day.date}</div>
                  <div className="flex-1 space-y-2">
                    {day.tasks.map((task, taskIndex) => (
                      <div key={taskIndex} className="flex items-center space-x-2 text-sm">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <span>{task}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
