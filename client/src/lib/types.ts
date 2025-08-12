import type { UploadJob, ProcessedResult } from "@shared/schema";

export interface FileUpload {
  file: File;
  id: string;
  status: 'ready' | 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  error?: string | null;
}

export interface PlatformSelection {
  [key: string]: boolean;
}

export { type UploadJob, type ProcessedResult };
