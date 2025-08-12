import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { UploadJob, PLATFORM_CONFIGS } from "@shared/schema";
import { Download, CheckCircle, Clock, AlertCircle } from "lucide-react";

interface ProcessingStatusProps {
  jobs: UploadJob[];
  onDownload: (jobId: string) => void;
  onDownloadAll: (jobId: string) => void;
}

export default function ProcessingStatus({ jobs, onDownload, onDownloadAll }: ProcessingStatusProps) {
  if (jobs.length === 0) return null;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-accent" />;
      case 'processing':
        return <Clock className="w-5 h-5 text-primary animate-pulse" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-destructive" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return 'Complete';
      case 'processing': return 'Processing...';
      case 'failed': return 'Failed';
      default: return 'Pending';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-accent';
      case 'processing': return 'text-primary';
      case 'failed': return 'text-destructive';
      default: return 'text-gray-500';
    }
  };

  const getPlatformIcon = (platformId: string) => {
    const platform = PLATFORM_CONFIGS.find(p => p.id === platformId.toLowerCase());
    if (!platform) return null;
    
    const iconClass = `w-6 h-6 rounded-md flex items-center justify-center ${
      platform.color.startsWith('from-') ? `bg-gradient-to-br ${platform.color}` : platform.color
    }`;

    // Return simplified platform icons
    return (
      <div className={iconClass}>
        <div className="w-3 h-3 bg-white rounded-sm" />
      </div>
    );
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
      <div className="mb-6">
        <h3 className="text-2xl font-semibold text-gray-900 mb-2">Processing Status</h3>
        <p className="text-gray-600">AI is analyzing and optimizing your media for each platform</p>
      </div>

      <div className="space-y-4">
        {jobs.map((job) => (
          <div 
            key={job.id} 
            className={`border rounded-lg p-4 ${
              job.status === 'completed' ? 'border-accent/30 bg-accent/5' : 'border-gray-200'
            }`}
            data-testid={`job-${job.id}`}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                  {job.mimeType.startsWith('image/') ? (
                    <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
                <div>
                  <p className="font-medium text-gray-900" data-testid={`job-filename-${job.id}`}>
                    {job.originalFileName}
                  </p>
                  <p className="text-sm text-gray-500" data-testid={`job-platforms-${job.id}`}>
                    Processing for {job.platforms.length} platform{job.platforms.length > 1 ? 's' : ''}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="flex items-center space-x-2 mb-1">
                  {getStatusIcon(job.status)}
                  <span className={`text-sm font-medium ${getStatusColor(job.status)}`} data-testid={`job-status-${job.id}`}>
                    {getStatusText(job.status)}
                  </span>
                </div>
                {job.status === 'processing' && (
                  <p className="text-xs text-gray-500" data-testid={`job-progress-${job.id}`}>
                    {job.progress}% complete
                  </p>
                )}
                {job.error && (
                  <p className="text-xs text-destructive" data-testid={`job-error-${job.id}`}>
                    {job.error}
                  </p>
                )}
              </div>
            </div>
            
            {/* Progress Bar */}
            {job.status === 'processing' && (
              <div className="mb-3">
                <Progress value={job.progress} className="h-2" data-testid={`job-progress-bar-${job.id}`} />
              </div>
            )}

            {/* Platform Status */}
            <div className="grid grid-cols-2 gap-3 mb-3">
              {job.platforms.map((platformId) => {
                const isCompleted = job.status === 'completed';
                return (
                  <div key={platformId} className="flex items-center space-x-2">
                    {getPlatformIcon(platformId)}
                    <span className={`text-sm ${
                      isCompleted ? 'text-accent font-medium' : 'text-gray-600'
                    }`} data-testid={`platform-status-${platformId}-${job.id}`}>
                      {PLATFORM_CONFIGS.find(p => p.id === platformId)?.name || platformId}
                      {isCompleted && ' ✓'}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Action Buttons */}
            {job.status === 'completed' && job.results && job.results.length > 0 && (
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onDownload(job.id)}
                  className="flex-1"
                  data-testid={`button-preview-${job.id}`}
                >
                  <Download className="w-4 h-4 mr-2" />
                  Preview Results
                </Button>
                <Button
                  size="sm"
                  onClick={() => onDownloadAll(job.id)}
                  className="flex-1 bg-accent hover:bg-accent/90"
                  data-testid={`button-download-all-${job.id}`}
                >
                  Download All ({job.results.length} files)
                </Button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
