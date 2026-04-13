// Represents a file selected for upload, with per-file upload state
export interface UploadFile {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'registering' | 'done' | 'error';
  progress: number;
  error?: string;
}

// VideoStatus values match the backend VideoStatus enum
export type VideoStatus =
  | 'pending'
  | 'processing'
  | 'completed'
  | 'flagged'
  | 'ready'
  | 'failed'
  | 'deleted';

export type VideoSource = 'upload' | 'api' | 'live' | 'url';

// Matches backend VideoResponse schema
export interface Video {
  id: string;
  title?: string;
  filename?: string;
  description?: string;
  source: VideoSource;
  status: VideoStatus;
  duration?: number;
  duration_seconds?: number;
  file_size_bytes?: number;
  content_type?: string;
  source_url?: string;
  s3_key?: string;
  thumbnail_s3_key?: string;
  thumbnail_url?: string;
  playback_url?: string;
  moderation_status?: string;
  owner_id?: string;
  tenant_id?: string;
  created_at: string;
  updated_at: string;
}

// Matches backend PaginatedVideos — no data wrapper
export interface VideoListResponse {
  items: Video[];
  total: number;
  page: number;
  page_size: number;
}

// GET /videos/{id} returns Video directly — no data wrapper
export type VideoResponse = Video;

export interface UploadUrlRequest {
  filename: string;
  content_type: string;
  file_size_bytes?: number;
}

// Matches backend UploadUrlResponse — no data wrapper
export interface UploadUrlResponse {
  upload_url: string;
  s3_key: string;
  expires_in: number;
}

// Matches backend VideoCreate schema
export interface RegisterUploadRequest {
  title: string;
  source: 'upload';
  s3_key: string;
  content_type?: string;
  file_size_bytes?: number;
  description?: string;
  tags?: string[];
}

// POST /videos returns the full Video object
export type RegisterUploadResponse = Video;

export interface VideoListParams {
  page?: number;
  page_size?: number;
  status?: VideoStatus;
  tenant_id?: string;
}
