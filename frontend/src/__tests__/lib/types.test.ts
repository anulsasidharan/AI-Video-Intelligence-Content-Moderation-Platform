/**
 * F-15 — TypeScript type definitions runtime tests
 * Validates that type shapes and constants are correct at runtime.
 */
import { VIDEO_STATUS_LABELS, MODERATION_STATUS_LABELS, ROUTES } from '@/lib/constants';
import type { Video, VideoStatus, VideoListResponse } from '@/types/video';
import type { ModerationStatus, Policy, Violation } from '@/types/moderation';
import type { User } from '@/types/user';

describe('Video types (F-15)', () => {
  it('VIDEO_STATUS_LABELS covers all VideoStatus values', () => {
    const statuses: VideoStatus[] = ['pending', 'processing', 'completed', 'failed', 'flagged'];
    statuses.forEach((s) => {
      expect(VIDEO_STATUS_LABELS[s]).toBeDefined();
      expect(typeof VIDEO_STATUS_LABELS[s]).toBe('string');
    });
  });

  it('VideoListResponse shape is correct at runtime', () => {
    const resp: VideoListResponse = {
      data: { items: [], total: 0, page: 1, page_size: 20 },
    };
    expect(resp.data.items).toBeInstanceOf(Array);
    expect(typeof resp.data.total).toBe('number');
  });

  it('Video object satisfies interface shape', () => {
    const video: Video = {
      id: 'v1',
      filename: 'clip.mp4',
      status: 'completed',
      source: 'upload',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };
    expect(video.id).toBe('v1');
    expect(video.status).toBe('completed');
  });
});

describe('Moderation types (F-15)', () => {
  it('MODERATION_STATUS_LABELS covers all ModerationStatus values', () => {
    const statuses: ModerationStatus[] = [
      'pending', 'in_review', 'approved', 'rejected', 'escalated',
    ];
    statuses.forEach((s) => {
      expect(MODERATION_STATUS_LABELS[s]).toBeDefined();
    });
  });

  it('Violation object satisfies interface shape', () => {
    const v: Violation = {
      id: 'viol-1',
      category: 'violence',
      confidence: 0.95,
    };
    expect(v.category).toBe('violence');
    expect(v.confidence).toBeGreaterThan(0);
  });

  it('Policy object satisfies interface shape', () => {
    const policy: Policy = {
      id: 'pol-1',
      name: 'Strict',
      categories: ['violence'],
      rules: [{ category: 'violence', threshold: 0.8, action: 'auto_reject' }],
      actions: ['auto_reject'],
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };
    expect(policy.rules).toHaveLength(1);
    expect(policy.is_active).toBe(true);
  });
});

describe('ROUTES constants (F-15)', () => {
  it('all static routes are strings', () => {
    expect(typeof ROUTES.home).toBe('string');
    expect(typeof ROUTES.dashboard).toBe('string');
    expect(typeof ROUTES.videos).toBe('string');
    expect(typeof ROUTES.moderationQueue).toBe('string');
    expect(typeof ROUTES.live).toBe('string');
    expect(typeof ROUTES.billing).toBe('string');
    expect(typeof ROUTES.adminRevenue).toBe('string');
    expect(typeof ROUTES.adminSubscribers).toBe('string');
  });

  it('dynamic routes are functions returning strings', () => {
    expect(ROUTES.videoDetail('abc')).toBe('/videos/abc');
    expect(ROUTES.liveStream('xyz')).toBe('/live/xyz');
  });
});

describe('User type (F-15)', () => {
  it('User object satisfies interface shape', async () => {
    const { } = await import('@/types/user');
    const user: User = {
      id: 'u1',
      email: 'admin@vidshield.ai',
      name: 'Admin User',
      role: 'admin',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };
    expect(user.email).toContain('@');
    expect(['admin', 'operator']).toContain(user.role);
  });
});
