'use client';

import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api';
import type {
  Video,
  VideoListResponse,
  VideoListParams,
  UploadUrlRequest,
  UploadUrlResponse,
  RegisterUploadRequest,
  UploadFile,
} from '@/types/video';
import { useVideoStore } from '@/stores/videoStore';

export const videoKeys = {
  all: ['videos'] as const,
  list: (params: VideoListParams) => ['videos', 'list', params] as const,
  detail: (id: string) => ['videos', 'detail', id] as const,
};

export function useVideoList(params: VideoListParams = {}) {
  return useQuery({
    queryKey: videoKeys.list(params),
    queryFn: () => apiClient.get<VideoListResponse>('/videos', { params }),
    staleTime: 60_000,
  });
}

export function useVideo(id: string) {
  return useQuery({
    queryKey: videoKeys.detail(id),
    queryFn: () => apiClient.get<Video>(`/videos/${id}`),
    enabled: !!id,
  });
}

export function useDeleteVideo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/videos/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: videoKeys.all });
      toast.success('Video deleted');
    },
    onError: () => {
      toast.error('Failed to delete video');
    },
  });
}

export function useAnalyzeUrl() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: { url: string; title?: string }) =>
      apiClient.post<Video>('/videos/analyze-url', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: videoKeys.all });
      toast.success('URL queued for AI analysis');
    },
    onError: () => {
      toast.error('Failed to submit URL. Check that it is a supported video link.');
    },
  });
}

export function useBulkDeleteVideos() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (videoIds: string[]) =>
      apiClient.post<{ deleted: number; skipped: number }>('/videos/bulk-delete', {
        video_ids: videoIds,
      }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: videoKeys.all });
      toast.success(
        result.deleted === 1
          ? '1 video file deleted — metadata and thumbnail retained'
          : `${result.deleted} video files deleted — metadata and thumbnails retained`
      );
    },
    onError: () => {
      toast.error('Bulk delete failed. Please try again.');
    },
  });
}

interface DuplicateCheckItem { filename: string; file_size_bytes: number; }
interface DuplicateCheckResult { filename: string; file_size_bytes: number; exists: boolean; }

export async function checkDuplicates(files: UploadFile[]): Promise<Set<string>> {
  const payload: DuplicateCheckItem[] = files.map((f) => ({
    filename: f.file.name,
    file_size_bytes: f.file.size,
  }));
  const results = await apiClient.post<DuplicateCheckResult[]>('/videos/check-duplicates', payload);
  return new Set(
    results.filter((r) => r.exists).map((r) => `${r.filename}-${r.file_size_bytes}`)
  );
}

type FileUpdateFn = (id: string, patch: Partial<Pick<UploadFile, 'status' | 'progress' | 'error'>>) => void;

export function useBulkUploadVideo() {
  const queryClient = useQueryClient();
  const { addUpload, updateUpload } = useVideoStore();
  const [isUploading, setIsUploading] = useState(false);

  const uploadAll = useCallback(
    async (files: UploadFile[], onUpdate: FileUpdateFn) => {
      const pending = files.filter((f) => f.status === 'pending' || f.status === 'error');
      if (pending.length === 0) return { succeeded: 0, failed: 0 };

      setIsUploading(true);

      const results = await Promise.allSettled(
        pending.map(async ({ id, file }) => {
          try {
            onUpdate(id, { status: 'uploading', progress: 0 });

            const urlRes = await apiClient.post<UploadUrlResponse>('/videos/upload-url', {
              filename: file.name,
              content_type: file.type,
              file_size_bytes: file.size,
            } as UploadUrlRequest);
            const { upload_url, s3_key } = urlRes;

            addUpload({ videoId: id, filename: file.name, progress: 0, status: 'uploading' });

            await axios.put(upload_url, file, {
              headers: { 'Content-Type': file.type },
              onUploadProgress: (e) => {
                const pct = e.total ? Math.round((e.loaded / e.total) * 100) : 0;
                onUpdate(id, { progress: pct });
                updateUpload(id, { progress: pct });
              },
            });

            onUpdate(id, { status: 'registering', progress: 100 });
            updateUpload(id, { status: 'registering', progress: 100 });

            await apiClient.post<Video>('/videos', {
              title: file.name,
              source: 'upload',
              s3_key,
              content_type: file.type,
              file_size_bytes: file.size,
            } as RegisterUploadRequest);

            onUpdate(id, { status: 'done' });
            updateUpload(id, { status: 'done' });
          } catch {
            onUpdate(id, { status: 'error', error: 'Upload failed' });
            updateUpload(id, { status: 'error', error: 'Upload failed' });
            throw new Error('Upload failed');
          }
        })
      );

      setIsUploading(false);

      const succeeded = results.filter((r) => r.status === 'fulfilled').length;
      const failed = results.length - succeeded;

      if (succeeded > 0) {
        queryClient.invalidateQueries({ queryKey: videoKeys.all });
        toast.success(
          succeeded === 1
            ? '1 video uploaded and queued for processing'
            : `${succeeded} videos uploaded and queued for processing`
        );
      }
      if (failed > 0) {
        toast.error(`${failed} video${failed > 1 ? 's' : ''} failed to upload`);
      }

      return { succeeded, failed };
    },
    [queryClient, addUpload, updateUpload]
  );

  return { uploadAll, isUploading };
}

export function useUploadVideo() {
  const queryClient = useQueryClient();
  const { addUpload, updateUpload } = useVideoStore();

  return useMutation({
    mutationFn: async ({ file }: { file: File }) => {
      // 1. Get presigned S3 PUT URL from backend
      const urlReq: UploadUrlRequest = {
        filename: file.name,
        content_type: file.type,
        file_size_bytes: file.size,
      };
      const urlRes = await apiClient.post<UploadUrlResponse>('/videos/upload-url', urlReq);
      // Backend returns the object directly — no .data wrapper
      const { upload_url, s3_key } = urlRes;

      // Use a client-side temp ID for progress tracking (no video_id at this stage)
      const tempId = `${file.name}-${Date.now()}`;
      addUpload({ videoId: tempId, filename: file.name, progress: 0, status: 'uploading' });

      // 2. PUT file directly to S3 using the presigned URL
      // Must send the same Content-Type that was used to sign the URL
      await axios.put(upload_url, file, {
        headers: { 'Content-Type': file.type },
        onUploadProgress: (e) => {
          const progress = e.total ? Math.round((e.loaded / e.total) * 100) : 0;
          updateUpload(tempId, { progress });
        },
      });

      updateUpload(tempId, { status: 'registering', progress: 100 });

      // 3. Register the video in the backend database
      const regReq: RegisterUploadRequest = {
        title: file.name,   // use filename as initial title; user can edit later
        source: 'upload',
        s3_key,             // use s3_key returned by upload-url endpoint
        content_type: file.type,
        file_size_bytes: file.size,
      };
      const video = await apiClient.post<Video>('/videos', regReq);

      updateUpload(tempId, { status: 'done' });
      return video;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: videoKeys.all });
      toast.success('Video uploaded and queued for processing');
    },
    onError: () => {
      toast.error('Upload failed. Please try again.');
    },
  });
}
