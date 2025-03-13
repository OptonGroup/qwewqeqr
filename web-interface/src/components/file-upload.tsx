import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, FileText, X, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { formatFileSize } from '@/utils';

interface FileUploadProps {
  onFileAccepted: (file: File) => void;
  maxSize?: number;
  allowedFileTypes?: string[];
}

export function FileUpload({
  onFileAccepted,
  maxSize = 5 * 1024 * 1024, // 5MB по умолчанию
  allowedFileTypes = ['.pdf', '.txt', '.csv'],
}: FileUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      setError(null);
      
      if (acceptedFiles.length === 0) {
        return;
      }

      const file = acceptedFiles[0];
      
      if (file.size > maxSize) {
        setError(`Файл слишком большой. Максимальный размер: ${formatFileSize(maxSize)}`);
        return;
      }

      const fileExtension = `.${file.name.split('.').pop()?.toLowerCase()}`;
      if (!allowedFileTypes.includes(fileExtension)) {
        setError(`Неподдерживаемый тип файла. Пожалуйста, загрузите файл в одном из следующих форматов: ${allowedFileTypes.join(', ')}`);
        return;
      }

      setSelectedFile(file);
    },
    [maxSize, allowedFileTypes]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles: 1,
    multiple: false,
  });

  const handleSubmit = () => {
    if (selectedFile) {
      onFileAccepted(selectedFile);
    }
  };

  const clearSelection = () => {
    setSelectedFile(null);
    setError(null);
  };

  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf':
        return <File className="h-8 w-8 text-blue-500" />;
      case 'txt':
        return <FileText className="h-8 w-8 text-green-500" />;
      case 'csv':
        return <FileText className="h-8 w-8 text-orange-500" />;
      default:
        return <File className="h-8 w-8 text-gray-500" />;
    }
  };

  return (
    <div className="w-full">
      {error && (
        <div className="mb-4 p-3 rounded-md bg-destructive/10 text-destructive flex items-start gap-2">
          <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {!selectedFile ? (
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-8 transition-colors duration-200
            ${isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/20'}
            hover:border-primary/50 hover:bg-primary/5 cursor-pointer text-center
          `}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center justify-center gap-4">
            <Upload className="h-10 w-10 text-muted-foreground" />
            <div className="space-y-2">
              <p className="text-xl font-medium">
                {isDragActive ? 'Перетащите файл сюда' : 'Загрузите банковскую выписку'}
              </p>
              <p className="text-sm text-muted-foreground">
                Перетащите файл сюда или нажмите для выбора
              </p>
              <p className="text-xs text-muted-foreground">
                Поддерживаемые форматы: {allowedFileTypes.join(', ')} | Макс. размер: {formatFileSize(maxSize)}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="border rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {getFileIcon(selectedFile.name)}
              <div>
                <p className="font-medium break-all">{selectedFile.name}</p>
                <p className="text-sm text-muted-foreground">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={clearSelection}
              aria-label="Удалить выбранный файл"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>
          <div className="mt-5">
            <Button onClick={handleSubmit} className="w-full">
              Обработать выписку
            </Button>
          </div>
        </div>
      )}
    </div>
  );
} 