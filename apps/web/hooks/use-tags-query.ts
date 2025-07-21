import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  TagsService,
  Tag,
  CreateTagRequest,
  UpdateTagRequest,
  BulkTagCreate,
} from '@/lib/api/tags';
import { useToast } from '@/hooks/use-toast';

// Query keys
export const tagsKeys = {
  all: ['tags'] as const,
  lists: () => [...tagsKeys.all, 'list'] as const,
  popular: () => [...tagsKeys.all, 'popular'] as const,
  details: () => [...tagsKeys.all, 'detail'] as const,
  detail: (id: string) => [...tagsKeys.details(), id] as const,
};

// Get all tags
export function useTagsQuery() {
  return useQuery({
    queryKey: tagsKeys.lists(),
    queryFn: () => TagsService.getTags(),
  });
}

// Get popular tags
export function usePopularTagsQuery(limit: number = 10) {
  return useQuery({
    queryKey: [...tagsKeys.popular(), { limit }],
    queryFn: () => TagsService.getPopularTags(limit),
  });
}

// Get single tag
export function useTagQuery(tagId: string, includeTasks: boolean = false) {
  return useQuery({
    queryKey: [...tagsKeys.detail(tagId), { includeTasks }],
    queryFn: () => TagsService.getTag(tagId, includeTasks),
    enabled: !!tagId,
  });
}

// Create tag mutation
export function useCreateTagMutation() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: CreateTagRequest) => TagsService.createTag(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tagsKeys.lists() });
      queryClient.invalidateQueries({ queryKey: tagsKeys.popular() });
      toast({
        title: 'Success',
        description: 'Tag created successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create tag',
        variant: 'destructive',
      });
    },
  });
}

// Create bulk tags mutation
export function useCreateBulkTagsMutation() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: BulkTagCreate) => TagsService.createBulkTags(data),
    onSuccess: (tags) => {
      queryClient.invalidateQueries({ queryKey: tagsKeys.lists() });
      queryClient.invalidateQueries({ queryKey: tagsKeys.popular() });
      toast({
        title: 'Success',
        description: `${tags.length} tags created successfully`,
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create tags',
        variant: 'destructive',
      });
    },
  });
}

// Update tag mutation
export function useUpdateTagMutation() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateTagRequest }) =>
      TagsService.updateTag(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: tagsKeys.lists() });
      queryClient.invalidateQueries({ queryKey: tagsKeys.popular() });
      queryClient.invalidateQueries({ queryKey: tagsKeys.detail(variables.id) });
      toast({
        title: 'Success',
        description: 'Tag updated successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update tag',
        variant: 'destructive',
      });
    },
  });
}

// Delete tag mutation
export function useDeleteTagMutation() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (tagId: string) => TagsService.deleteTag(tagId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tagsKeys.lists() });
      queryClient.invalidateQueries({ queryKey: tagsKeys.popular() });
      toast({
        title: 'Success',
        description: 'Tag deleted successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete tag',
        variant: 'destructive',
      });
    },
  });
}
