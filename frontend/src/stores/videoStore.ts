import { create } from 'zustand';
import type { Video } from '@/types/video';

interface UploadProgress {
  videoId: string;
  filename: string;
  progress: number;
  status: 'uploading' | 'registering' | 'done' | 'error';
  error?: string;
}

interface VideoState {
  selectedVideoId: string | null;
  uploads: UploadProgress[];
}

interface VideoActions {
  selectVideo: (id: string | null) => void;
  addUpload: (upload: UploadProgress) => void;
  updateUpload: (videoId: string, patch: Partial<UploadProgress>) => void;
  removeUpload: (videoId: string) => void;
  clearUploads: () => void;
}

export const useVideoStore = create<VideoState & VideoActions>()((set) => ({
  selectedVideoId: null,
  uploads: [],

  selectVideo: (id) => set({ selectedVideoId: id }),

  addUpload: (upload) =>
    set((state) => ({ uploads: [...state.uploads, upload] })),

  updateUpload: (videoId, patch) =>
    set((state) => ({
      uploads: state.uploads.map((u) =>
        u.videoId === videoId ? { ...u, ...patch } : u
      ),
    })),

  removeUpload: (videoId) =>
    set((state) => ({
      uploads: state.uploads.filter((u) => u.videoId !== videoId),
    })),

  clearUploads: () => set({ uploads: [] }),
}));

// Selector helpers — wrap with useShallow() at call sites to avoid
// infinite re-render loops from .filter() returning new array references.
export const selectActiveUploads = (state: VideoState & VideoActions) =>
  state.uploads.filter((u) => u.status === 'uploading' || u.status === 'registering');
