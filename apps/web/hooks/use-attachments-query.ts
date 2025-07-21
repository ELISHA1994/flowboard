import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AttachmentsService, FileAttachment } from '@/lib/api/attachments';
import { useToastContext } from '@/contexts/toast-context';

// Query keys factory
export const attachmentKeys = {
  all: ['attachments'] as const,
  lists: () => [...attachmentKeys.all, 'list'] as const,
  list: (taskId: string) => [...attachmentKeys.lists(), taskId] as const,
  details: () => [...attachmentKeys.all, 'detail'] as const,
  detail: (id: string) => [...attachmentKeys.details(), id] as const,
  limits: () => [...attachmentKeys.all, 'limits'] as const,
};

// Get task attachments
export function useTaskAttachments(taskId: string) {
  return useQuery({
    queryKey: attachmentKeys.list(taskId),
    queryFn: () => AttachmentsService.getTaskAttachments(taskId),
    enabled: !!taskId,
  });
}

// Upload attachment
export function useUploadAttachmentMutation() {
  const queryClient = useQueryClient();
  const { toast } = useToastContext();

  return useMutation({
    mutationFn: ({ taskId, file }: { taskId: string; file: File }) =>
      AttachmentsService.uploadAttachment(taskId, file),
    onSuccess: (data, variables) => {
      // Invalidate task attachments list
      queryClient.invalidateQueries({ queryKey: attachmentKeys.list(variables.taskId) });

      toast({
        title: 'File uploaded',
        description: `${data.original_filename} has been uploaded successfully.`,
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Upload failed',
        description: error.message || 'Failed to upload file. Please try again.',
        variant: 'destructive',
      });
    },
  });
}

// Delete attachment
export function useDeleteAttachmentMutation() {
  const queryClient = useQueryClient();
  const { toast } = useToastContext();

  return useMutation({
    mutationFn: ({ attachmentId, taskId }: { attachmentId: string; taskId: string }) =>
      AttachmentsService.deleteAttachment(attachmentId),
    onSuccess: (_, variables) => {
      // Invalidate task attachments list
      queryClient.invalidateQueries({ queryKey: attachmentKeys.list(variables.taskId) });

      toast({
        title: 'File deleted',
        description: 'The attachment has been deleted successfully.',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Delete failed',
        description: error.message || 'Failed to delete attachment. Please try again.',
        variant: 'destructive',
      });
    },
  });
}

// Get upload limits
export function useUploadLimits() {
  return useQuery({
    queryKey: attachmentKeys.limits(),
    queryFn: () => AttachmentsService.getUploadLimits(),
    staleTime: 60 * 60 * 1000, // 1 hour
  });
}
