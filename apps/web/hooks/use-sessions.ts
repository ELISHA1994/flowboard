import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AuthService, SessionInfo } from '@/lib/auth';
import { useToast } from '@/hooks/use-toast';

export function useSessionsQuery() {
  return useQuery<SessionInfo[]>({
    queryKey: ['sessions'],
    queryFn: () => AuthService.getSessions(),
    // Refetch sessions every 30 seconds
    refetchInterval: 30000,
  });
}

export function useRevokeSessionMutation() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (sessionId: string) => AuthService.revokeSession(sessionId),
    onSuccess: (_, sessionId) => {
      // Optimistically remove the session from cache
      queryClient.setQueryData<SessionInfo[]>(['sessions'], (old) =>
        old ? old.filter((session) => session.id !== sessionId) : []
      );

      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['sessions'] });

      toast({
        title: 'Session revoked',
        description: 'The selected session has been signed out.',
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to revoke session. Please try again.',
        variant: 'destructive',
      });
    },
  });
}

export function useLogoutAllMutation() {
  const { toast } = useToast();

  return useMutation({
    mutationFn: () => AuthService.logoutAll(),
    onSuccess: () => {
      toast({
        title: 'All sessions revoked',
        description: 'You have been signed out from all devices.',
      });

      // Redirect to login after a short delay
      setTimeout(() => {
        window.location.href = '/login';
      }, 1500);
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to sign out from all devices. Please try again.',
        variant: 'destructive',
      });
    },
  });
}
