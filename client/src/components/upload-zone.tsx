import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Button } from "@/components/ui/button";
import { FileUpload } from "@/lib/types";
import { X, Upload } from "lucide-react";

interface UploadZoneProps {
  files: FileUpload[];
  onFilesAdded: (files: File[]) => void;
  onFileRemoved: (fileId: string) => void;
}

export default function UploadZone({ files, onFilesAdded, onFileRemoved }: UploadZoneProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    onFilesAdded(acceptedFiles);
  }, [onFilesAdded]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.webp'],
      'video/*': ['.mp4', '.mov']
    },
    maxSize: 500 * 1024 * 1024, // 500MB
    multiple: true
  });

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('video/')) {
      return (
        <div className="w-12 h-12 bg-gradient-to-br from-purple-400 to-purple-600 rounded-lg flex items-center justify-center">
          <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
          </svg>
        </div>
      );
    } else {
      return (
        <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-blue-600 rounded-lg flex items-center justify-center">
          <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
          </svg>
        </div>
      );
    }
  };

  const getStatusColor = (status: FileUpload['status']) => {
    switch (status) {
      case 'ready': return 'text-accent';
      case 'uploading': return 'text-primary';
      case 'processing': return 'text-primary';
      case 'completed': return 'text-accent';
      case 'error': return 'text-destructive';
      default: return 'text-gray-500';
    }
  };

  const getStatusText = (status: FileUpload['status']) => {
    switch (status) {
      case 'ready': return 'Ready';
      case 'uploading': return 'Uploading...';
      case 'processing': return 'Processing...';
      case 'completed': return 'Completed';
      case 'error': return 'Error';
      default: return 'Unknown';
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
      <div className="mb-6">
        <h3 className="text-2xl font-semibold text-gray-900 mb-2">Upload Your Media</h3>
        <p className="text-gray-600">Support for JPG, PNG, MP4, MOV files up to 500MB</p>
      </div>
      
      {/* Drag and Drop Zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
          isDragActive 
            ? 'border-primary bg-primary/10' 
            : 'border-gray-300 hover:border-primary hover:bg-gray-50'
        }`}
        data-testid="upload-zone"
      >
        <input {...getInputProps()} />
        <div className="mx-auto w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
          <Upload className="w-8 h-8 text-gray-400" />
        </div>
        <h4 className="text-lg font-medium text-gray-900 mb-2">Drop your files here</h4>
        <p className="text-gray-500 mb-4">or click to browse from your device</p>
        <Button type="button" data-testid="button-browse">
          Browse Files
        </Button>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-3 mt-6">
          {files.map((fileUpload) => (
            <div key={fileUpload.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg" data-testid={`file-item-${fileUpload.id}`}>
              <div className="flex items-center space-x-3">
                {getFileIcon(fileUpload.file)}
                <div>
                  <p className="font-medium text-gray-900" data-testid={`file-name-${fileUpload.id}`}>
                    {fileUpload.file.name}
                  </p>
                  <p className="text-sm text-gray-500" data-testid={`file-size-${fileUpload.id}`}>
                    {formatFileSize(fileUpload.file.size)}
                    {fileUpload.file.type.startsWith('video/') && ' • Video'}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`text-sm font-medium ${getStatusColor(fileUpload.status)}`} data-testid={`file-status-${fileUpload.id}`}>
                  {getStatusText(fileUpload.status)}
                </span>
                {fileUpload.status === 'processing' && (
                  <div className="text-xs text-gray-500" data-testid={`file-progress-${fileUpload.id}`}>
                    {fileUpload.progress}%
                  </div>
                )}
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => onFileRemoved(fileUpload.id)}
                  className="text-gray-400 hover:text-gray-600"
                  data-testid={`button-remove-${fileUpload.id}`}
                >
                  <X className="w-5 h-5" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
