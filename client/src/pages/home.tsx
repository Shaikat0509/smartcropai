import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import Header from "@/components/header";
import Footer from "@/components/footer";
import UploadZone from "@/components/upload-zone";
import PlatformSelector from "@/components/platform-selector";
import ProcessingStatus from "@/components/processing-status";
import MediaPreview from "@/components/media-preview";
import { FileUpload, PlatformSelection, UploadJob } from "@/lib/types";

export default function Home() {
  const [files, setFiles] = useState<FileUpload[]>([]);
  const [selectedPlatforms, setSelectedPlatforms] = useState<PlatformSelection>({
    instagram: true,
    facebook: true,
  });
  
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Fetch all upload jobs
  const { data: jobs = [] } = useQuery<UploadJob[]>({
    queryKey: ['/api/jobs'],
    refetchInterval: 2000, // Poll every 2 seconds for updates
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async ({ file, platforms }: { file: File; platforms: string[] }) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('platforms', JSON.stringify(platforms));
      
      const response = await apiRequest('POST', '/api/upload', formData);
      return response.json();
    },
    onSuccess: (data: UploadJob) => {
      // Update file status
      setFiles(prev => prev.map(f => 
        f.file.name === data.originalFileName 
          ? { ...f, status: 'processing' }
          : f
      ));
      
      queryClient.invalidateQueries({ queryKey: ['/api/jobs'] });
      toast({
        title: "Upload Started",
        description: `Processing ${data.originalFileName} for ${data.platforms.length} platforms`,
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Upload Failed",
        description: error.message,
        variant: "destructive",
      });
      
      // Reset file status on error
      setFiles(prev => prev.map(f => ({ ...f, status: 'error' })));
    },
  });

  const handleFilesAdded = (newFiles: File[]) => {
    const fileUploads: FileUpload[] = newFiles.map(file => ({
      file,
      id: `${file.name}-${Date.now()}`,
      status: 'ready',
      progress: 0,
    }));
    
    setFiles(prev => [...prev, ...fileUploads]);
  };

  const handleFileRemoved = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const handleProcess = async () => {
    const selectedPlatformIds = Object.entries(selectedPlatforms)
      .filter(([_, selected]) => selected)
      .map(([platformId]) => platformId);

    if (files.length === 0) {
      toast({
        title: "No Files",
        description: "Please upload at least one file",
        variant: "destructive",
      });
      return;
    }

    if (selectedPlatformIds.length === 0) {
      toast({
        title: "No Platforms",
        description: "Please select at least one platform",
        variant: "destructive",
      });
      return;
    }

    // Update file status to uploading
    setFiles(prev => prev.map(f => ({ ...f, status: 'uploading' as const })));

    // Process each file
    for (const fileUpload of files) {
      try {
        await uploadMutation.mutateAsync({
          file: fileUpload.file,
          platforms: selectedPlatformIds,
        });
      } catch (error) {
        console.error(`Failed to upload ${fileUpload.file.name}:`, error);
      }
    }
  };

  const handleDownload = async (jobId: string, filename: string) => {
    try {
      const response = await fetch(`/api/download/${jobId}/${filename}`);
      if (!response.ok) throw new Error('Download failed');
      
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      toast({
        title: "Download Failed",
        description: "Failed to download file",
        variant: "destructive",
      });
    }
  };

  const handleDownloadAll = async (jobId: string) => {
    try {
      const response = await apiRequest('GET', `/api/download-all/${jobId}`);
      const data = await response.json();
      
      if (data.files && data.files.length > 0) {
        // Download each file individually (in production, you'd create a zip)
        for (const file of data.files) {
          await handleDownload(jobId, file.filename);
        }
        
        toast({
          title: "Download Complete",
          description: `Downloaded ${data.files.length} files`,
        });
      }
    } catch (error) {
      toast({
        title: "Download Failed",
        description: "Failed to download files",
        variant: "destructive",
      });
    }
  };

  // Update file progress based on job status
  const updatedFiles = files.map(fileUpload => {
    const job = jobs.find(j => j.originalFileName === fileUpload.file.name);
    if (job) {
      return {
        ...fileUpload,
        status: job.status === 'processing' ? 'processing' as const :
                job.status === 'completed' ? 'completed' as const :
                job.status === 'failed' ? 'error' as const : fileUpload.status,
        progress: job.progress,
        error: job.error,
      };
    }
    return fileUpload;
  });

  const completedJobs = jobs.filter(job => job.status === 'completed' && job.results);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            Resize Your Media for
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary"> Every Platform</span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Upload once, get perfect sizes for Instagram, TikTok, YouTube, Facebook, LinkedIn, and more. 
            AI-powered smart cropping keeps your content looking great everywhere.
          </p>
        </div>

        {/* Upload Section */}
        <div className="mb-8">
          <UploadZone
            files={updatedFiles}
            onFilesAdded={handleFilesAdded}
            onFileRemoved={handleFileRemoved}
          />
        </div>

        {/* Platform Selection */}
        <div className="mb-8">
          <PlatformSelector
            selectedPlatforms={selectedPlatforms}
            onSelectionChange={setSelectedPlatforms}
            onProcess={handleProcess}
            hasFiles={files.length > 0}
          />
        </div>

        {/* Processing Status */}
        {jobs.length > 0 && (
          <div className="mb-8">
            <ProcessingStatus
              jobs={jobs}
              onDownload={(jobId) => {
                const job = jobs.find(j => j.id === jobId);
                if (job?.results?.[0]) {
                  const filename = job.results[0].filePath.split('/').pop() || '';
                  handleDownload(jobId, filename);
                }
              }}
              onDownloadAll={handleDownloadAll}
            />
          </div>
        )}

        {/* Results Preview */}
        {completedJobs.map(job => (
          job.results && (
            <div key={job.id} className="mb-8">
              <MediaPreview
                results={job.results}
                jobId={job.id}
                onDownload={handleDownload}
                onDownloadAll={handleDownloadAll}
              />
            </div>
          )
        ))}

        {/* Features Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
          <div className="text-center">
            <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">AI-Powered Smart Crop</h3>
            <p className="text-gray-600">Automatically detects and keeps important subjects in frame across all aspect ratios.</p>
          </div>

          <div className="text-center">
            <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Multi-Platform Output</h3>
            <p className="text-gray-600">Generate perfect sizes for Instagram, TikTok, YouTube, Facebook, LinkedIn, and more in one click.</p>
          </div>

          <div className="text-center">
            <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Optimized File Sizes</h3>
            <p className="text-gray-600">Automatic compression and optimization ensures fast uploads while maintaining quality.</p>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
