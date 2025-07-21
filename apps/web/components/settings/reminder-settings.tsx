'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Bell,
  Mail,
  Smartphone,
  Clock,
  Calendar,
  Settings,
  AlertCircle,
  Loader2,
  CheckCircle2,
} from 'lucide-react';
import {
  useNotificationPreferences,
  useUpdateNotificationPreferencesMutation,
} from '@/hooks/use-reminders';
import { NotificationPreferencesUpdate } from '@/lib/api/reminders';

export function ReminderSettings() {
  const { data: preferences, isLoading, error } = useNotificationPreferences();
  const updatePreferencesMutation = useUpdateNotificationPreferencesMutation();

  const [localPreferences, setLocalPreferences] = useState<NotificationPreferencesUpdate>({});

  // Update local preferences when data loads
  React.useEffect(() => {
    if (preferences) {
      setLocalPreferences({
        in_app_notifications: preferences.in_app_notifications,
        email_notifications: preferences.email_notifications,
        notification_frequency: preferences.notification_frequency,
        reminder_notifications: preferences.reminder_notifications,
        task_assignment_notifications: preferences.task_assignment_notifications,
        task_completion_notifications: preferences.task_completion_notifications,
        comment_notifications: preferences.comment_notifications,
        project_notifications: preferences.project_notifications,
      });
    }
  }, [preferences]);

  const handlePreferenceChange = (key: keyof NotificationPreferencesUpdate, value: any) => {
    setLocalPreferences((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    await updatePreferencesMutation.mutateAsync(localPreferences);
  };

  const hasUnsavedChanges = () => {
    if (!preferences) return false;
    return Object.keys(localPreferences).some(
      (key) =>
        localPreferences[key as keyof NotificationPreferencesUpdate] !==
        preferences[key as keyof typeof preferences]
    );
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-3">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>Loading notification preferences...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-6">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Failed to load notification preferences. Please try refreshing the page.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Notification Channels */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Notification Channels
          </CardTitle>
          <CardDescription>Choose how you want to receive notifications</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between space-x-2">
            <div className="flex items-center space-x-2">
              <Bell className="h-4 w-4 text-blue-600" />
              <div className="space-y-1">
                <Label htmlFor="in-app">In-App Notifications</Label>
                <p className="text-sm text-muted-foreground">
                  Receive notifications within the application
                </p>
              </div>
            </div>
            <Switch
              id="in-app"
              checked={localPreferences.in_app_notifications ?? true}
              onCheckedChange={(checked) => handlePreferenceChange('in_app_notifications', checked)}
            />
          </div>

          <div className="flex items-center justify-between space-x-2">
            <div className="flex items-center space-x-2">
              <Mail className="h-4 w-4 text-green-600" />
              <div className="space-y-1">
                <Label htmlFor="email">Email Notifications</Label>
                <p className="text-sm text-muted-foreground">Receive notifications via email</p>
              </div>
            </div>
            <Switch
              id="email"
              checked={localPreferences.email_notifications ?? true}
              onCheckedChange={(checked) => handlePreferenceChange('email_notifications', checked)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Notification Frequency */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Notification Frequency
          </CardTitle>
          <CardDescription>Control how often you receive non-urgent notifications</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label>Delivery Frequency</Label>
            <Select
              value={localPreferences.notification_frequency ?? 'immediate'}
              onValueChange={(value) => handlePreferenceChange('notification_frequency', value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="immediate">
                  <div className="flex items-center gap-2">
                    <Bell className="h-4 w-4" />
                    <div>
                      <div>Immediate</div>
                      <div className="text-xs text-muted-foreground">
                        Receive notifications as they happen
                      </div>
                    </div>
                  </div>
                </SelectItem>
                <SelectItem value="daily_digest">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    <div>
                      <div>Daily Digest</div>
                      <div className="text-xs text-muted-foreground">Once per day summary</div>
                    </div>
                  </div>
                </SelectItem>
                <SelectItem value="weekly_digest">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    <div>
                      <div>Weekly Digest</div>
                      <div className="text-xs text-muted-foreground">Once per week summary</div>
                    </div>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Note: Urgent notifications (like reminders) are always delivered immediately
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Notification Types */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Notification Types
          </CardTitle>
          <CardDescription>Choose which types of notifications you want to receive</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between space-x-2">
            <div className="flex items-center space-x-2">
              <Bell className="h-4 w-4 text-orange-600" />
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Label htmlFor="reminders">Task Reminders</Label>
                  <Badge variant="secondary" className="text-xs">
                    Important
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">
                  Notifications for task reminders and due dates
                </p>
              </div>
            </div>
            <Switch
              id="reminders"
              checked={localPreferences.reminder_notifications ?? true}
              onCheckedChange={(checked) =>
                handlePreferenceChange('reminder_notifications', checked)
              }
            />
          </div>

          <div className="flex items-center justify-between space-x-2">
            <div className="flex items-center space-x-2">
              <Smartphone className="h-4 w-4 text-blue-600" />
              <div className="space-y-1">
                <Label htmlFor="assignments">Task Assignments</Label>
                <p className="text-sm text-muted-foreground">When you're assigned to a new task</p>
              </div>
            </div>
            <Switch
              id="assignments"
              checked={localPreferences.task_assignment_notifications ?? true}
              onCheckedChange={(checked) =>
                handlePreferenceChange('task_assignment_notifications', checked)
              }
            />
          </div>

          <div className="flex items-center justify-between space-x-2">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <div className="space-y-1">
                <Label htmlFor="completions">Task Completions</Label>
                <p className="text-sm text-muted-foreground">
                  When tasks you're involved in are completed
                </p>
              </div>
            </div>
            <Switch
              id="completions"
              checked={localPreferences.task_completion_notifications ?? true}
              onCheckedChange={(checked) =>
                handlePreferenceChange('task_completion_notifications', checked)
              }
            />
          </div>

          <div className="flex items-center justify-between space-x-2">
            <div className="flex items-center space-x-2">
              <Bell className="h-4 w-4 text-purple-600" />
              <div className="space-y-1">
                <Label htmlFor="comments">Comments & Mentions</Label>
                <p className="text-sm text-muted-foreground">
                  When someone mentions you or comments on your tasks
                </p>
              </div>
            </div>
            <Switch
              id="comments"
              checked={localPreferences.comment_notifications ?? true}
              onCheckedChange={(checked) =>
                handlePreferenceChange('comment_notifications', checked)
              }
            />
          </div>

          <div className="flex items-center justify-between space-x-2">
            <div className="flex items-center space-x-2">
              <Bell className="h-4 w-4 text-teal-600" />
              <div className="space-y-1">
                <Label htmlFor="projects">Project Updates</Label>
                <p className="text-sm text-muted-foreground">
                  Updates about projects you're a member of
                </p>
              </div>
            </div>
            <Switch
              id="projects"
              checked={localPreferences.project_notifications ?? true}
              onCheckedChange={(checked) =>
                handlePreferenceChange('project_notifications', checked)
              }
            />
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      {hasUnsavedChanges() && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-amber-600">
                <AlertCircle className="h-4 w-4" />
                <span className="text-sm">You have unsaved changes</span>
              </div>
              <Button onClick={handleSave} disabled={updatePreferencesMutation.isPending}>
                {updatePreferencesMutation.isPending && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Save Preferences
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
