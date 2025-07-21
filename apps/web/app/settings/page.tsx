import { DashboardLayout } from '@/components/layouts/dashboard-layout';

export default function SettingsPage() {
  return (
    <DashboardLayout>
      <div className="flex-1 space-y-4 p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
        </div>
        <div className="rounded-lg border bg-card p-8">
          <p className="text-muted-foreground">
            Settings page coming soon. This will allow you to configure your account and
            preferences.
          </p>
        </div>
      </div>
    </DashboardLayout>
  );
}
