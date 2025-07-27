import { useCallback, useState } from 'react';
import { CloudArrowUpIcon, XMarkIcon, DocumentIcon } from '@heroicons/react/24/outline';
import { cn, formatFileSize } from '../../utils/helpers';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  onFileRemove?: () => void;
  accept?: string;
  maxSize?: number; // in MB
  currentFile?: File | null;
  isUploading?: boolean;
  className?: string;
}

export function FileUpload({
  onFileSelect,
  onFileRemove,
  accept = 'image/*',
  maxSize = 10,
  currentFile,
  isUploading = false,
  className,
}: FileUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateFile = useCallback((file: File): string | null => {
    // Check file type
    if (accept && !file.type.match(accept.replace('*', '.*'))) {
      return `File type not supported. Please select ${accept} files.`;
    }

    // Check file size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > maxSize) {
      return `File size must be less than ${maxSize}MB.`;
    }

    return null;
  }, [accept, maxSize]);

  const handleFileSelect = useCallback((file: File) => {
    const error = validateFile(file);
    if (error) {
      setError(error);
      return;
    }

    setError(null);
    onFileSelect(file);
  }, [validateFile, onFileSelect]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  const handleRemove = useCallback(() => {
    setError(null);
    onFileRemove?.();
  }, [onFileRemove]);

  // Show selected file preview
  if (currentFile) {
    return (
      <div className={cn('relative', className)}>
        <div className="border-2 border-gray-300 dark:border-gray-600 border-dashed rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                {currentFile.type.startsWith('image/') ? (
                  <img
                    src={URL.createObjectURL(currentFile)}
                    alt="Preview"
                    className="h-16 w-16 object-cover rounded-md"
                  />
                ) : (
                  <DocumentIcon className="h-16 w-16 text-gray-400" />
                )}
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {currentFile.name}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {formatFileSize(currentFile.size)}
                </p>
              </div>
            </div>
            {!isUploading && (
              <button
                onClick={handleRemove}
                className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-500 dark:hover:text-gray-300"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            )}
          </div>
          {isUploading && (
            <div className="mt-4">
              <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '45%' }}></div>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                Processing your formula...
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={cn('relative', className)}>
      <div
        className={cn(
          'dropzone border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer',
          isDragOver ? 'active' : 'border-gray-300 dark:border-gray-600',
          error && 'border-red-300 dark:border-red-600'
        )}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        <input
          id="file-input"
          type="file"
          accept={accept}
          onChange={handleInputChange}
          className="hidden"
        />
        
        <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
        <div className="mt-4">
          <p className="text-lg font-medium text-gray-900 dark:text-white">
            Drop your formula image here
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            or click to browse files
          </p>
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
            Supports: JPG, PNG, GIF (max {maxSize}MB)
          </p>
        </div>
      </div>

      {error && (
        <p className="mt-2 text-sm text-red-600 dark:text-red-400">
          {error}
        </p>
      )}
    </div>
  );
}