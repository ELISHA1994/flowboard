'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState } from 'react';

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Stale time: how long before data is considered stale
            staleTime: 30 * 1000, // 30 seconds
            // Cache time: how long to keep data in cache after it's unused
            cacheTime: 5 * 60 * 1000, // 5 minutes
            // Refetch on window focus - keeps data fresh when user returns
            refetchOnWindowFocus: true,
            // Refetch on reconnect - sync after network issues
            refetchOnReconnect: true,
            // Retry failed requests with exponential backoff
            retry: 3,
            retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
          },
          mutations: {
            // Retry mutations only once
            retry: 1,
            // Show error notifications
            onError: (error) => {
              console.error('Mutation error:', error);
            },
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
