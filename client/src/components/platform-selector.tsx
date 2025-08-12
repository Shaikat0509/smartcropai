import { useState } from "react";
import { Button } from "@/components/ui/button";
import { PLATFORM_CONFIGS } from "@shared/schema";
import { PlatformSelection } from "@/lib/types";
import { Check } from "lucide-react";

interface PlatformSelectorProps {
  selectedPlatforms: PlatformSelection;
  onSelectionChange: (platforms: PlatformSelection) => void;
  onProcess: () => void;
  hasFiles: boolean;
}

export default function PlatformSelector({ 
  selectedPlatforms, 
  onSelectionChange, 
  onProcess, 
  hasFiles 
}: PlatformSelectorProps) {
  
  const togglePlatform = (platformId: string) => {
    onSelectionChange({
      ...selectedPlatforms,
      [platformId]: !selectedPlatforms[platformId]
    });
  };

  const selectAll = () => {
    const allSelected = PLATFORM_CONFIGS.reduce((acc, platform) => ({
      ...acc,
      [platform.id]: true
    }), {});
    onSelectionChange(allSelected);
  };

  const selectedCount = Object.values(selectedPlatforms).filter(Boolean).length;

  const getPlatformIcon = (iconName: string) => {
    switch (iconName) {
      case 'instagram':
        return (
          <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
          </svg>
        );
      case 'tiktok':
        return (
          <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M19.321 5.562a5.122 5.122 0 01-.443-.258 6.228 6.228 0 01-1.137-.966c-.849-1.067-1.233-2.45-1.233-2.45h-3.014v14.66c0 1.049-.402 2.019-1.132 2.735-.729.717-1.693 1.111-2.716 1.111-2.114 0-3.847-1.711-3.847-3.847 0-2.135 1.732-3.846 3.847-3.846.397 0 .778.064 1.137.182V9.756a7.83 7.83 0 00-1.137-.084c-4.318 0-7.847 3.503-7.847 7.847 0 4.344 3.529 7.847 7.847 7.847 4.318 0 7.847-3.503 7.847-7.847V8.917c1.388.992 3.077 1.565 4.847 1.625V6.542c-1.062 0-2.065-.386-2.847-1.08z"/>
          </svg>
        );
      case 'youtube':
        return (
          <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
          </svg>
        );
      case 'facebook':
        return (
          <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
          </svg>
        );
      case 'linkedin':
        return (
          <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
          </svg>
        );
      case 'pinterest':
        return (
          <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12.017 0C5.396 0 .029 5.367.029 11.987c0 5.079 3.158 9.417 7.618 11.174-.105-.949-.199-2.403.041-3.439.219-.937 1.404-5.965 1.404-5.965s-.359-.72-.359-1.781c0-1.663.967-2.911 2.168-2.911 1.024 0 1.518.769 1.518 1.688 0 1.029-.653 2.567-.992 3.992-.285 1.193.6 2.165 1.775 2.165 2.128 0 3.768-2.245 3.768-5.487 0-2.861-2.063-4.869-5.008-4.869-3.41 0-5.409 2.562-5.409 5.199 0 1.033.394 2.143.889 2.741.097.118.112.221.085.345-.09.375-.293 1.199-.334 1.363-.053.225-.172.271-.402.165-1.495-.69-2.433-2.878-2.433-4.646 0-3.776 2.748-7.252 7.92-7.252 4.158 0 7.392 2.967 7.392 6.923 0 4.135-2.607 7.462-6.233 7.462-1.214 0-2.357-.629-2.747-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146C9.57 23.812 10.763 24.009 12.017 24c6.624 0 11.99-5.367 11.99-11.013C24.007 5.367 18.641.001 12.017.001z"/>
          </svg>
        );
      case 'twitter':
        return (
          <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
          </svg>
        );
      case 'monitor':
        return (
          <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3 5a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2h-2.22l.123.489.804.804A1 1 0 0113 18H7a1 1 0 01-.707-1.707l.804-.804L7.22 15H5a2 2 0 01-2-2V5zm5.771 7H5V5h10v7H8.771z" clipRule="evenodd" />
          </svg>
        );
      default:
        return null;
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
      <div className="mb-6">
        <h3 className="text-2xl font-semibold text-gray-900 mb-2">Select Platforms</h3>
        <p className="text-gray-600">Choose which platforms you want to optimize your media for</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {PLATFORM_CONFIGS.map((platform) => {
          const isSelected = selectedPlatforms[platform.id];
          return (
            <div
              key={platform.id}
              onClick={() => togglePlatform(platform.id)}
              className={`border-2 rounded-xl p-4 cursor-pointer transition-colors ${
                isSelected 
                  ? 'border-primary bg-primary/5' 
                  : 'border-gray-200 hover:border-primary hover:bg-gray-50'
              }`}
              data-testid={`platform-${platform.id}`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                  platform.color.startsWith('from-') ? `bg-gradient-to-br ${platform.color}` : platform.color
                }`}>
                  {getPlatformIcon(platform.icon)}
                </div>
                {isSelected && (
                  <Check className="w-5 h-5 text-primary" data-testid={`check-${platform.id}`} />
                )}
              </div>
              <h4 className="font-semibold text-gray-900 mb-1">{platform.name}</h4>
              <p className="text-xs text-gray-500">
                {platform.formats.map(f => f.name).join(', ')}
              </p>
              <p className={`text-xs font-medium mt-1 ${
                isSelected ? 'text-primary' : 'text-gray-600'
              }`}>
                {platform.formats.map(f => f.aspectRatio).join(', ')}
              </p>
            </div>
          );
        })}
      </div>

      <div className="mt-6 flex justify-between items-center">
        <Button 
          variant="ghost" 
          onClick={selectAll}
          data-testid="button-select-all"
        >
          Select All
        </Button>
        <Button
          onClick={onProcess}
          disabled={!hasFiles || selectedCount === 0}
          data-testid="button-process"
        >
          Process Media ({selectedCount} platform{selectedCount !== 1 ? 's' : ''} selected)
        </Button>
      </div>
    </div>
  );
}
