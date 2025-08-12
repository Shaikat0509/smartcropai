import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { ProcessedResult, PLATFORM_CONFIGS } from "@shared/schema";
import { Download, Eye } from "lucide-react";

interface MediaPreviewProps {
  results: ProcessedResult[];
  jobId: string;
  onDownload: (jobId: string, filename: string) => void;
  onDownloadAll: (jobId: string) => void;
}

export default function MediaPreview({ results, jobId, onDownload, onDownloadAll }: MediaPreviewProps) {
  const [selectedResult, setSelectedResult] = useState<ProcessedResult | null>(null);

  if (!results || results.length === 0) return null;

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const getPlatformColor = (platformName: string) => {
    const platform = PLATFORM_CONFIGS.find(p => p.name.toLowerCase() === platformName.toLowerCase());
    return platform?.color || 'bg-gray-600';
  };

  const getPlatformIcon = (platformName: string) => {
    const platform = PLATFORM_CONFIGS.find(p => p.name.toLowerCase() === platformName.toLowerCase());
    if (!platform) return null;
    
    const iconClass = `w-6 h-6 rounded-md flex items-center justify-center ${
      platform.color.startsWith('from-') ? `bg-gradient-to-br ${platform.color}` : platform.color
    }`;

    return (
      <div className={iconClass}>
        <div className="w-3 h-3 bg-white rounded-sm" />
      </div>
    );
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
      <div className="mb-6">
        <h3 className="text-2xl font-semibold text-gray-900 mb-2">Preview Results</h3>
        <p className="text-gray-600">Preview your optimized media before downloading</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {results.map((result, index) => (
          <div 
            key={`${result.platform}-${result.format}-${index}`} 
            className="border border-gray-200 rounded-lg p-4"
            data-testid={`preview-${result.platform}-${result.format}`}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                {getPlatformIcon(result.platform)}
                <span className="text-sm font-medium text-gray-900">
                  {result.platform} {result.format}
                </span>
              </div>
              <span className="text-xs text-gray-500">
                {result.dimensions.width}×{result.dimensions.height}
              </span>
            </div>
            
            {/* Preview placeholder - in production this would show actual images */}
            <div 
              className="bg-gray-100 rounded-lg mb-3 overflow-hidden flex items-center justify-center"
              style={{
                aspectRatio: `${result.dimensions.width}/${result.dimensions.height}`,
                minHeight: '120px'
              }}
            >
              <div className="text-center text-gray-500">
                <Eye className="w-8 h-8 mx-auto mb-2" />
                <p className="text-xs">Preview</p>
                <p className="text-xs">{result.format}</p>
              </div>
            </div>
            
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs text-accent font-medium">
                {result.optimized ? 'Optimized' : 'Processed'}
              </span>
              <span className="text-xs text-gray-500">
                {formatFileSize(result.fileSize)}
              </span>
            </div>

            <Dialog>
              <DialogTrigger asChild>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="w-full mb-2"
                  onClick={() => setSelectedResult(result)}
                  data-testid={`button-preview-${result.platform}-${result.format}`}
                >
                  <Eye className="w-4 h-4 mr-2" />
                  Preview
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-4xl">
                <DialogHeader>
                  <DialogTitle>
                    {selectedResult?.platform} {selectedResult?.format} Preview
                  </DialogTitle>
                </DialogHeader>
                <div className="p-4">
                  <div className="bg-gray-100 rounded-lg aspect-video flex items-center justify-center">
                    <div className="text-center text-gray-500">
                      <Eye className="w-12 h-12 mx-auto mb-2" />
                      <p>Full Preview</p>
                      <p className="text-sm">{selectedResult?.dimensions.width}×{selectedResult?.dimensions.height}</p>
                    </div>
                  </div>
                </div>
              </DialogContent>
            </Dialog>

            <Button
              size="sm"
              className="w-full"
              onClick={() => onDownload(jobId, result.filePath.split('/').pop() || '')}
              data-testid={`button-download-${result.platform}-${result.format}`}
            >
              <Download className="w-4 h-4 mr-2" />
              Download
            </Button>
          </div>
        ))}
      </div>

      <div className="mt-6 flex flex-col sm:flex-row gap-3">
        <Button 
          variant="outline" 
          className="flex-1"
          data-testid="button-preview-all"
        >
          Preview All Formats
        </Button>
        <Button 
          className="flex-1 bg-accent hover:bg-accent/90"
          onClick={() => onDownloadAll(jobId)}
          data-testid="button-download-all-formats"
        >
          Download All ({results.length} files)
        </Button>
      </div>
    </div>
  );
}
