/**
 * F-03 — VideoCard component tests
 */
import { render, screen, fireEvent, within } from '@testing-library/react';
import React from 'react';
import { VideoCard } from '@/components/video/VideoCard';
import type { Video } from '@/types/video';

// Render Radix DropdownMenu inline (no portal) so jsdom can interact with it
jest.mock('@/components/ui/dropdown-menu', () => ({
  DropdownMenu: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuTrigger: ({ children, asChild }: { children: React.ReactNode; asChild?: boolean }) =>
    asChild ? <>{children}</> : <div>{children}</div>,
  DropdownMenuContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuItem: ({ children, onClick, className }: { children: React.ReactNode; onClick?: () => void; className?: string }) => (
    <button role="menuitem" onClick={onClick} className={className}>{children}</button>
  ),
}));

const baseVideo: Video = {
  id: 'vid-001',
  filename: 'test-video.mp4',
  title: 'My Test Video',
  status: 'completed',
  source: 'upload',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

describe('VideoCard (F-03)', () => {
  it('renders video title', () => {
    render(<VideoCard video={baseVideo} />);
    expect(screen.getByText('My Test Video')).toBeInTheDocument();
  });

  it('falls back to filename when title is absent', () => {
    const video = { ...baseVideo, title: undefined };
    render(<VideoCard video={video} />);
    expect(screen.getByText('test-video.mp4')).toBeInTheDocument();
  });

  it('renders the status badge with correct label', () => {
    render(<VideoCard video={baseVideo} />);
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('renders Film icon placeholder when no thumbnail', () => {
    render(<VideoCard video={baseVideo} />);
    // No img with src should be in the document for thumbnail
    const images = screen.queryAllByRole('img');
    const thumbnails = images.filter((img) =>
      (img as HTMLImageElement).alt === 'My Test Video'
    );
    expect(thumbnails).toHaveLength(0);
  });

  it('renders thumbnail image when thumbnail_url is set', () => {
    const video = { ...baseVideo, thumbnail_url: 'https://example.com/thumb.jpg' };
    render(<VideoCard video={video} />);
    const img = screen.getByAltText('My Test Video');
    expect(img).toBeInTheDocument();
  });

  it('calls onDelete with video id when delete is clicked', () => {
    const onDelete = jest.fn();
    render(<VideoCard video={baseVideo} onDelete={onDelete} />);
    // With the mocked DropdownMenu, menu items render inline
    const deleteItem = screen.getByRole('menuitem', { name: /delete/i });
    fireEvent.click(deleteItem);
    expect(onDelete).toHaveBeenCalledWith('vid-001');
  });

  it('does not render delete button when onDelete is not provided', () => {
    render(<VideoCard video={baseVideo} />);
    expect(screen.queryByLabelText('Video actions')).not.toBeInTheDocument();
  });

  it('renders duration badge when duration is set', () => {
    const video = { ...baseVideo, duration: 90 };
    render(<VideoCard video={video} />);
    // formatDuration(90) = "1:30"
    expect(screen.getByText('1:30')).toBeInTheDocument();
  });

  it('renders different status labels', () => {
    const statuses: Array<[Video['status'], string]> = [
      ['pending', 'Pending'],
      ['processing', 'Processing'],
      ['failed', 'Failed'],
      ['flagged', 'Flagged'],
    ];
    statuses.forEach(([status, label]) => {
      const { unmount } = render(<VideoCard video={{ ...baseVideo, status }} />);
      expect(screen.getByText(label)).toBeInTheDocument();
      unmount();
    });
  });
});
