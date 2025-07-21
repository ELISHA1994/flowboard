import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  CategoriesService,
  Category,
  CreateCategoryRequest,
  UpdateCategoryRequest,
} from '@/lib/api/categories';
import { useToast } from '@/hooks/use-toast';

// Query keys
export const categoriesKeys = {
  all: ['categories'] as const,
  lists: () => [...categoriesKeys.all, 'list'] as const,
  list: (includeInactive?: boolean) => [...categoriesKeys.lists(), { includeInactive }] as const,
  details: () => [...categoriesKeys.all, 'detail'] as const,
  detail: (id: string) => [...categoriesKeys.details(), id] as const,
};

// Get all categories
export function useCategoriesQuery(includeInactive: boolean = false) {
  return useQuery({
    queryKey: categoriesKeys.list(includeInactive),
    queryFn: () => CategoriesService.getCategories(includeInactive),
  });
}

// Get single category
export function useCategoryQuery(categoryId: string, includeTasks: boolean = false) {
  return useQuery({
    queryKey: [...categoriesKeys.detail(categoryId), { includeTasks }],
    queryFn: () => CategoriesService.getCategory(categoryId, includeTasks),
    enabled: !!categoryId,
  });
}

// Create category mutation
export function useCreateCategoryMutation() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: CreateCategoryRequest) => CategoriesService.createCategory(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: categoriesKeys.lists() });
      toast({
        title: 'Success',
        description: 'Category created successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create category',
        variant: 'destructive',
      });
    },
  });
}

// Update category mutation
export function useUpdateCategoryMutation() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateCategoryRequest }) =>
      CategoriesService.updateCategory(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: categoriesKeys.lists() });
      queryClient.invalidateQueries({ queryKey: categoriesKeys.detail(variables.id) });
      toast({
        title: 'Success',
        description: 'Category updated successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update category',
        variant: 'destructive',
      });
    },
  });
}

// Delete category mutation
export function useDeleteCategoryMutation() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (categoryId: string) => CategoriesService.deleteCategory(categoryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: categoriesKeys.lists() });
      toast({
        title: 'Success',
        description: 'Category deleted successfully',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete category',
        variant: 'destructive',
      });
    },
  });
}
