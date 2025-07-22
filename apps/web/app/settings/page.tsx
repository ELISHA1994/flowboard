import { DashboardLayout } from '@/components/layouts/dashboard-layout';
import { ReminderSettings } from '@/components/settings/reminder-settings';
import { SessionManagement } from '@/components/settings/session-management';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function SettingsPage() {
  return (
    <DashboardLayout>
      <div className="flex-1 space-y-4 p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
        </div>

        <Tabs defaultValue="notifications" className="space-y-4">
          <TabsList>
            <TabsTrigger value="notifications">Notifications</TabsTrigger>
            <TabsTrigger value="security">Security</TabsTrigger>
          </TabsList>

          <TabsContent value="notifications" className="space-y-4">
            <ReminderSettings />
          </TabsContent>

          <TabsContent value="security" className="space-y-4">
            <SessionManagement />
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}
