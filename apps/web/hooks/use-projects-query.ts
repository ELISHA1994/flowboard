'use client';

import { useQuery } from '@tanstack/react-query';

export interface Project {
  id: string;
  name: string;
  description?: string;
}

interface ProjectsResponse {
  projects: Project[];
  total: number;
}

// Temporary stub implementation until projects API is available
export function useProjectsQuery() {
  return useQuery<ProjectsResponse>({
    queryKey: ['projects'],
    queryFn: async () => {
      // TODO: Replace with actual API call when projects endpoint is implemented
      // For now, return empty list to fix build error
      return {
        projects: [],
        total: 0,
      };
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
