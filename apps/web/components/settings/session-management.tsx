'use client';

import React from 'react';
import { formatDistanceToNow } from 'date-fns';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Monitor,
  Smartphone,
  Tablet,
  Shield,
  Loader2,
  AlertCircle,
  RefreshCw,
  Globe,
  Clock,
  LogOut,
} from 'lucide-react';
import {
  useSessionsQuery,
  useRevokeSessionMutation,
  useLogoutAllMutation,
} from '@/hooks/use-sessions';
import { SessionInfo } from '@/lib/auth';

function getDeviceIcon(deviceType?: string | null) {
  switch (deviceType?.toLowerCase()) {
    case 'mobile':
      return <Smartphone className="h-4 w-4" />;
    case 'tablet':
      return <Tablet className="h-4 w-4" />;
    case 'desktop':
    default:
      return <Monitor className="h-4 w-4" />;
  }
}

function SessionCard({ session }: { session: SessionInfo }) {
  const revokeSessionMutation = useRevokeSessionMutation();
  const [showIp, setShowIp] = React.useState(false);

  const lastActiveText = session.last_active
    ? formatDistanceToNow(new Date(session.last_active), { addSuffix: true })
    : 'Unknown';

  const createdText = formatDistanceToNow(new Date(session.created_at), { addSuffix: true });

  return (
    <Card className={session.is_current ? 'border-primary' : ''}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-2">
              {getDeviceIcon(session.device_type)}
              <span className="font-medium">{session.device_name || 'Unknown Device'}</span>
              {session.is_current && (
                <Badge variant="default" className="ml-2">
                  Current Session
                </Badge>
              )}
            </div>

            <div className="space-y-1 text-sm text-muted-foreground">
              {session.browser && (
                <div className="flex items-center gap-2">
                  <Globe className="h-3 w-3" />
                  <span>{session.browser}</span>
                </div>
              )}

              {session.ip_address && (
                <div className="flex items-center gap-2">
                  <Shield className="h-3 w-3" />
                  <button
                    onClick={() => setShowIp(!showIp)}
                    className="hover:text-foreground transition-colors"
                  >
                    {showIp ? session.ip_address : 'IP: •••.•••.•••.•••'}
                  </button>
                </div>
              )}

              <div className="flex items-center gap-2">
                <Clock className="h-3 w-3" />
                <span>{session.is_current ? 'Active now' : `Last active ${lastActiveText}`}</span>
              </div>

              <div className="text-xs">Started {createdText}</div>
            </div>
          </div>

          {!session.is_current && (
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="outline" size="sm" disabled={revokeSessionMutation.isPending}>
                  {revokeSessionMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <LogOut className="h-4 w-4" />
                  )}
                  <span className="ml-2">Sign Out</span>
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Sign out this device?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This will sign out the session on {session.device_name || 'this device'}. Any
                    unsaved work on that device will be lost.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={() => revokeSessionMutation.mutate(session.id)}>
                    Sign Out Device
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function SessionManagement() {
  const { data: sessions, isLoading, error, refetch } = useSessionsQuery();
  const logoutAllMutation = useLogoutAllMutation();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Active Sessions
          </CardTitle>
          <CardDescription>Loading your active sessions...</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
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
              Failed to load active sessions. Please try refreshing the page.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  const otherSessions = sessions?.filter((s) => !s.is_current) || [];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Active Sessions
            </CardTitle>
            <CardDescription>Manage your active sessions across different devices</CardDescription>
          </div>
          <Button variant="ghost" size="icon" onClick={() => refetch()} title="Refresh sessions">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {!sessions || sessions.length === 0 ? (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              No active sessions found. This might happen if you just logged in.
            </AlertDescription>
          </Alert>
        ) : (
          <>
            <div className="space-y-3">
              {sessions.map((session) => (
                <SessionCard key={session.id} session={session} />
              ))}
            </div>

            {otherSessions.length > 0 && (
              <div className="pt-4 border-t">
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="destructive" className="w-full">
                      Sign Out All Other Sessions
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Sign out all other devices?</AlertDialogTitle>
                      <AlertDialogDescription>
                        This will sign you out from all devices except this one. You'll need to sign
                        in again on those devices.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction
                        onClick={() => logoutAllMutation.mutate()}
                        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                      >
                        Sign Out All Devices
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
