import { ApiClient } from '@/lib/api-client';

export interface FileAttachment {
  id: string;
  task_id: string;
  uploaded_by_id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type?: string;
  created_at: string;
  uploaded_by?: {
    id: string;
    username: string;
    email: string;
  };
}

export interface FileUploadLimits {
  max_file_size: number;
  allowed_file_types: string[];
}

export class AttachmentsService {
  static async uploadAttachment(taskId: string, file: File): Promise<FileAttachment> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await ApiClient.fetchWithAuth(
      ApiClient.buildUrl(`/tasks/${taskId}/attachments`),
      {
        method: 'POST',
        body: formData,
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(error.detail || `Upload failed with status ${response.status}`);
    }

    return response.json();
  }

  static async getTaskAttachments(
    taskId: string
  ): Promise<{ attachments: FileAttachment[]; total: number }> {
    return ApiClient.fetchJSON(ApiClient.buildUrl(`/tasks/${taskId}/attachments`));
  }

  static async downloadAttachment(attachmentId: string): Promise<void> {
    try {
      const response = await ApiClient.fetchWithAuth(
        ApiClient.buildUrl(`/attachments/${attachmentId}/download`)
      );

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Download failed' }));
        throw new Error(error.detail || `Download failed with status ${response.status}`);
      }

      // Get filename from Content-Disposition header if available
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'download';
      if (contentDisposition) {
        const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (match && match[1]) {
          filename = match[1].replace(/['"]/g, '');
        }
      }

      // Create blob from response
      const blob = await response.blob();

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();

      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download error:', error);
      throw error;
    }
  }

  static async deleteAttachment(attachmentId: string): Promise<void> {
    await ApiClient.fetchJSON(ApiClient.buildUrl(`/attachments/${attachmentId}`), {
      method: 'DELETE',
    });
  }

  static async getUploadLimits(): Promise<FileUploadLimits> {
    return ApiClient.fetchJSON(ApiClient.buildUrl(`/attachments/limits`));
  }

  static formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  static getFileIcon(mimeType?: string, filename?: string): string {
    if (!mimeType && filename) {
      const ext = filename.split('.').pop()?.toLowerCase();
      if (ext) {
        mimeType = this.getMimeTypeFromExtension(ext);
      }
    }

    if (!mimeType) return 'file';

    if (mimeType.startsWith('image/')) return 'image';
    if (mimeType.startsWith('video/')) return 'video';
    if (mimeType.startsWith('audio/')) return 'audio';
    if (mimeType === 'application/pdf') return 'file-text';
    if (mimeType.includes('spreadsheet') || mimeType.includes('excel')) return 'file-spreadsheet';
    if (mimeType.includes('document') || mimeType.includes('word')) return 'file-text';
    if (mimeType.includes('presentation') || mimeType.includes('powerpoint'))
      return 'file-presentation';
    if (mimeType.includes('zip') || mimeType.includes('compressed')) return 'file-archive';
    if (mimeType.includes('text/')) return 'file-code';

    return 'file';
  }

  private static getMimeTypeFromExtension(ext: string): string {
    const mimeTypes: Record<string, string> = {
      // Images
      jpg: 'image/jpeg',
      jpeg: 'image/jpeg',
      png: 'image/png',
      gif: 'image/gif',
      svg: 'image/svg+xml',
      webp: 'image/webp',

      // Documents
      pdf: 'application/pdf',
      doc: 'application/msword',
      docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      xls: 'application/vnd.ms-excel',
      xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      ppt: 'application/vnd.ms-powerpoint',
      pptx: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',

      // Archives
      zip: 'application/zip',
      rar: 'application/x-rar-compressed',
      '7z': 'application/x-7z-compressed',
      tar: 'application/x-tar',
      gz: 'application/gzip',

      // Code
      js: 'text/javascript',
      ts: 'text/typescript',
      py: 'text/x-python',
      java: 'text/x-java',
      cpp: 'text/x-c++',
      c: 'text/x-c',
      html: 'text/html',
      css: 'text/css',
      json: 'application/json',
      xml: 'application/xml',

      // Media
      mp3: 'audio/mpeg',
      wav: 'audio/wav',
      mp4: 'video/mp4',
      avi: 'video/x-msvideo',
      mov: 'video/quicktime',

      // Other
      txt: 'text/plain',
      csv: 'text/csv',
    };

    return mimeTypes[ext] || 'application/octet-stream';
  }
}
