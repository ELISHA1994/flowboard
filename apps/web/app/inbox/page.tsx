import { DashboardLayout } from '@/components/layouts/dashboard-layout';

export default function InboxPage() {
  return (
    <DashboardLayout>
      <div className="flex-1 space-y-4 p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">Inbox</h2>
        </div>
        <div className="rounded-lg border bg-card p-8">
          <p className="text-muted-foreground">
            Inbox page coming soon. This will display your notifications and messages.
          </p>
        </div>
      </div>
    </DashboardLayout>
  );
}
