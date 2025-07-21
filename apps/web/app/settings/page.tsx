import { DashboardLayout } from '@/components/layouts/dashboard-layout';
import { ReminderSettings } from '@/components/settings/reminder-settings';

export default function SettingsPage() {
  return (
    <DashboardLayout>
      <div className="flex-1 space-y-4 p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
        </div>
        <ReminderSettings />
      </div>
    </DashboardLayout>
  );
}
