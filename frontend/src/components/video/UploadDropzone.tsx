'use client';

import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { AlertCircle, CheckCircle2, CloudUpload, File, Loader2, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { cn, formatBytes } from '@/lib/utils';
import { ACCEPTED_VIDEO_TYPES, MAX_UPLOAD_SIZE_BYTES } from '@/lib/constants';
import type { UploadFile } from '@/types/video';

export type { UploadFile };

interface UploadDropzoneProps {
  files: UploadFile[];
  onFilesAdded: (files: UploadFile[]) => void;
  onFileRemove: (id: string) => void;
  disabled?: boolean;
}

export function UploadDropzone({
  files,
  onFilesAdded,
  onFileRemove,
  disabled = false,
}: UploadDropzoneProps) {
  const isActive = files.some(
    (f) => f.status === 'uploading' || f.status === 'registering'
  );

  const onDrop = useCallback(
    (accepted: File[]) => {
      const newFiles: UploadFile[] = accepted.map((f) => ({
        file: f,
        id: `${f.name}-${f.size}-${Date.now()}-${Math.random()}`,
        status: 'pending',
        progress: 0,
      }));
      onFilesAdded(newFiles);
    },
    [onFilesAdded]
  );

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: Object.fromEntries(ACCEPTED_VIDEO_TYPES.map((t) => [t, []])),
    maxSize: MAX_UPLOAD_SIZE_BYTES,
    multiple: true,
    disabled: disabled || isActive,
  });

  return (
    <div className="space-y-4">
      {/* Drop area */}
      <div
        {...getRootProps()}
        className={cn(
          'flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-colors',
          isDragActive
            ? 'border-primary bg-primary/5'
            : 'border-border hover:border-primary/50 hover:bg-accent/30',
          (disabled || isActive) && 'cursor-not-allowed opacity-50'
        )}
      >
        <input {...getInputProps()} />
        <CloudUpload className="mb-3 h-10 w-10 text-muted-foreground" />
        <p className="text-sm font-medium">
          {isDragActive ? 'Drop videos here' : 'Drag & drop videos, or click to select'}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          MP4, WebM, MOV, AVI, MKV — max {formatBytes(MAX_UPLOAD_SIZE_BYTES)} per file
        </p>
      </div>

      {/* Rejections */}
      {fileRejections.length > 0 && (
        <ul className="space-y-1">
          {fileRejections.map(({ file, errors }) => (
            <li key={file.name} className="text-xs text-destructive">
              {file.name}: {errors.map((e) => e.message).join(', ')}
            </li>
          ))}
        </ul>
      )}

      {/* File list */}
      {files.length > 0 && (
        <ul className="space-y-2">
          {files.map(({ file, id, status, progress, error }) => (
            <li
              key={id}
              className="flex items-center gap-3 rounded-md border bg-muted/30 px-4 py-3"
            >
              <File className="h-5 w-5 shrink-0 text-muted-foreground" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{file.name}</p>
                <p className="text-xs text-muted-foreground">{formatBytes(file.size)}</p>
                {status === 'uploading' && (
                  <Progress value={progress} className="mt-2 h-1.5" />
                )}
                {status === 'registering' && (
                  <p className="mt-1 text-xs text-muted-foreground">Registering…</p>
                )}
                {status === 'error' && (
                  <p className="mt-1 text-xs text-destructive">{error ?? 'Upload failed'}</p>
                )}
              </div>

              {/* Status icon */}
              <div className="shrink-0">
                {(status === 'uploading' || status === 'registering') && (
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                )}
                {status === 'done' && (
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                )}
                {status === 'error' && (
                  <AlertCircle className="h-4 w-4 text-destructive" />
                )}
                {status === 'pending' && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={() => onFileRemove(id)}
                    aria-label={`Remove ${file.name}`}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
