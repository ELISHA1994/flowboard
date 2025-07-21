import { DashboardLayout } from '@/components/layouts/dashboard-layout';

export default function CalendarPage() {
  return (
    <DashboardLayout>
      <div className="flex-1 space-y-4 p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">Calendar</h2>
        </div>
        <div className="rounded-lg border bg-card p-8">
          <p className="text-muted-foreground">
            Calendar page coming soon. This will display your tasks in a calendar view.
          </p>
        </div>
      </div>
    </DashboardLayout>
  );
}
