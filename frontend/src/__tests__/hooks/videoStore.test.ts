/**
 * F-11 — Zustand videoStore tests
 */
import { act } from 'react';
import { useVideoStore, selectActiveUploads } from '@/stores/videoStore';

beforeEach(() => {
  // Reset store state between tests
  useVideoStore.setState({ selectedVideoId: null, uploads: [] });
});

describe('useVideoStore (F-11)', () => {
  it('starts with empty uploads and no selected video', () => {
    const state = useVideoStore.getState();
    expect(state.uploads).toEqual([]);
    expect(state.selectedVideoId).toBeNull();
  });

  it('selectVideo() sets selectedVideoId', () => {
    act(() => {
      useVideoStore.getState().selectVideo('vid-123');
    });
    expect(useVideoStore.getState().selectedVideoId).toBe('vid-123');
  });

  it('selectVideo(null) clears selection', () => {
    useVideoStore.setState({ selectedVideoId: 'vid-123' });
    act(() => {
      useVideoStore.getState().selectVideo(null);
    });
    expect(useVideoStore.getState().selectedVideoId).toBeNull();
  });

  it('addUpload() appends a new upload entry', () => {
    act(() => {
      useVideoStore.getState().addUpload({
        videoId: 'vid-001',
        filename: 'clip.mp4',
        progress: 0,
        status: 'uploading',
      });
    });
    expect(useVideoStore.getState().uploads).toHaveLength(1);
    expect(useVideoStore.getState().uploads[0].videoId).toBe('vid-001');
  });

  it('updateUpload() patches matching upload entry', () => {
    useVideoStore.setState({
      uploads: [{ videoId: 'vid-001', filename: 'clip.mp4', progress: 0, status: 'uploading' }],
    });
    act(() => {
      useVideoStore.getState().updateUpload('vid-001', { progress: 50 });
    });
    expect(useVideoStore.getState().uploads[0].progress).toBe(50);
  });

  it('removeUpload() removes matching upload entry', () => {
    useVideoStore.setState({
      uploads: [
        { videoId: 'vid-001', filename: 'clip.mp4', progress: 100, status: 'done' },
        { videoId: 'vid-002', filename: 'other.mp4', progress: 50, status: 'uploading' },
      ],
    });
    act(() => {
      useVideoStore.getState().removeUpload('vid-001');
    });
    expect(useVideoStore.getState().uploads).toHaveLength(1);
    expect(useVideoStore.getState().uploads[0].videoId).toBe('vid-002');
  });

  it('clearUploads() empties the uploads list', () => {
    useVideoStore.setState({
      uploads: [
        { videoId: 'vid-001', filename: 'a.mp4', progress: 100, status: 'done' },
        { videoId: 'vid-002', filename: 'b.mp4', progress: 100, status: 'done' },
      ],
    });
    act(() => {
      useVideoStore.getState().clearUploads();
    });
    expect(useVideoStore.getState().uploads).toHaveLength(0);
  });

  it('selectActiveUploads selector returns only uploading/registering entries', () => {
    const state = {
      ...useVideoStore.getState(),
      uploads: [
        { videoId: 'v1', filename: 'a.mp4', progress: 50, status: 'uploading' as const },
        { videoId: 'v2', filename: 'b.mp4', progress: 100, status: 'done' as const },
        { videoId: 'v3', filename: 'c.mp4', progress: 30, status: 'registering' as const },
      ],
    };
    const active = selectActiveUploads(state);
    expect(active).toHaveLength(2);
    expect(active.map((u) => u.videoId)).toEqual(['v1', 'v3']);
  });
});
