'use client';

import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Upload,
  Paperclip,
  FileText,
  FileImage,
  FileVideo,
  FileAudio,
  FileSpreadsheetIcon,
  FileCode,
  FileArchive,
  File,
  Download,
  Trash2,
  MoreVertical,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { AttachmentsService } from '@/lib/api/attachments';
import {
  useTaskAttachments,
  useUploadAttachmentMutation,
  useDeleteAttachmentMutation,
  useUploadLimits,
} from '@/hooks/use-attachments-query';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';

interface TaskAttachmentsProps {
  taskId: string;
  canEdit?: boolean;
}

export function TaskAttachments({ taskId, canEdit = true }: TaskAttachmentsProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [deleteAttachmentId, setDeleteAttachmentId] = useState<string | null>(null);
  const [deleteAttachmentName, setDeleteAttachmentName] = useState<string>('');

  // React Query hooks
  const { data: attachmentsData, isLoading } = useTaskAttachments(taskId);
  const { data: uploadLimits } = useUploadLimits();
  const uploadMutation = useUploadAttachmentMutation();
  const deleteMutation = useDeleteAttachmentMutation();

  const attachments = attachmentsData?.attachments || [];

  // Handle file selection
  const handleFileSelect = (files: FileList | null) => {
    if (!files || files.length === 0) return;

    // Validate files
    for (let i = 0; i < files.length; i++) {
      const file = files[i];

      // Check file size
      if (uploadLimits && file.size > uploadLimits.max_file_size) {
        const maxSizeFormatted = AttachmentsService.formatFileSize(uploadLimits.max_file_size);
        alert(`File "${file.name}" exceeds the maximum size of ${maxSizeFormatted}`);
        continue;
      }

      // Check file type
      const fileExt = `.${file.name.split('.').pop()?.toLowerCase()}`;
      if (uploadLimits && !uploadLimits.allowed_file_types.includes(fileExt)) {
        alert(
          `File type "${fileExt}" is not allowed. Allowed types: ${uploadLimits.allowed_file_types.join(', ')}`
        );
        continue;
      }

      // Upload file
      uploadMutation.mutate({ taskId, file });
    }
  };

  // Handle drag and drop
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (!canEdit) return;

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files);
    }
  };

  // Get file icon
  const getFileIcon = (mimeType?: string, filename?: string) => {
    const iconType = AttachmentsService.getFileIcon(mimeType, filename);

    const iconMap: Record<string, React.ReactNode> = {
      image: <FileImage className="h-5 w-5" />,
      video: <FileVideo className="h-5 w-5" />,
      audio: <FileAudio className="h-5 w-5" />,
      'file-text': <FileText className="h-5 w-5" />,
      'file-spreadsheet': <FileSpreadsheetIcon className="h-5 w-5" />,
      'file-code': <FileCode className="h-5 w-5" />,
      'file-archive': <FileArchive className="h-5 w-5" />,
      file: <File className="h-5 w-5" />,
    };

    return iconMap[iconType] || <File className="h-5 w-5" />;
  };

  // Handle delete
  const handleDelete = (attachmentId: string, filename: string) => {
    setDeleteAttachmentId(attachmentId);
    setDeleteAttachmentName(filename);
  };

  const confirmDelete = () => {
    if (deleteAttachmentId) {
      deleteMutation.mutate({ attachmentId: deleteAttachmentId, taskId });
      setDeleteAttachmentId(null);
      setDeleteAttachmentName('');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Upload area */}
      {canEdit && (
        <div
          className={cn(
            'relative rounded-lg border-2 border-dashed p-6 text-center transition-colors',
            dragActive
              ? 'border-primary bg-primary/5'
              : 'border-muted-foreground/25 hover:border-muted-foreground/50'
          )}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={(e) => handleFileSelect(e.target.files)}
            accept={uploadLimits?.allowed_file_types.join(',')}
          />

          <Upload className="mx-auto h-8 w-8 text-muted-foreground" />
          <p className="mt-2 text-sm font-medium">
            {dragActive ? 'Drop files here' : 'Drag and drop files here'}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            or{' '}
            <Button
              variant="link"
              size="sm"
              className="h-auto p-0"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadMutation.isPending}
            >
              browse files
            </Button>
          </p>

          {uploadLimits && (
            <p className="mt-2 text-xs text-muted-foreground">
              Max size: {AttachmentsService.formatFileSize(uploadLimits.max_file_size)} • Allowed:{' '}
              {uploadLimits.allowed_file_types.join(', ')}
            </p>
          )}

          {uploadMutation.isPending && (
            <div className="absolute inset-0 flex items-center justify-center rounded-lg bg-background/80">
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Uploading...</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Attachments list */}
      {attachments.length === 0 ? (
        <div className="text-center py-8">
          <Paperclip className="mx-auto h-8 w-8 text-muted-foreground/50" />
          <p className="mt-2 text-sm text-muted-foreground">No attachments yet</p>
          {canEdit && (
            <p className="text-xs text-muted-foreground">
              Upload files by dragging them here or clicking browse
            </p>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {attachments.map((attachment) => (
            <div
              key={attachment.id}
              className="flex items-center justify-between rounded-lg border p-3 hover:bg-muted/50"
            >
              <div className="flex items-center gap-3">
                <div className="text-muted-foreground">
                  {getFileIcon(attachment.mime_type, attachment.original_filename)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{attachment.original_filename}</p>
                  <p className="text-xs text-muted-foreground">
                    {AttachmentsService.formatFileSize(attachment.file_size)} • Uploaded by{' '}
                    {attachment.uploaded_by?.username || 'Unknown'} •
                    {format(new Date(attachment.created_at), 'MMM d, yyyy')}
                  </p>
                </div>
              </div>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem
                    onClick={() => AttachmentsService.downloadAttachment(attachment.id)}
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Download
                  </DropdownMenuItem>
                  {canEdit && (
                    <DropdownMenuItem
                      className="text-destructive"
                      onClick={() => handleDelete(attachment.id, attachment.original_filename)}
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete
                    </DropdownMenuItem>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          ))}
        </div>
      )}

      {/* Delete confirmation dialog */}
      <AlertDialog
        open={!!deleteAttachmentId}
        onOpenChange={(open) => {
          if (!open) {
            setDeleteAttachmentId(null);
            setDeleteAttachmentName('');
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete attachment?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{deleteAttachmentName}"? This action cannot be
              undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
