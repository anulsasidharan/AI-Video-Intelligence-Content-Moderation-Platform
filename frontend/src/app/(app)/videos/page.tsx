'use client';

import { useState } from 'react';
import Link from 'next/link';
import { CheckSquare, Plus, RefreshCw, Trash2, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { VideoCard } from '@/components/video/VideoCard';
import { useVideoList, useDeleteVideo, useBulkDeleteVideos } from '@/hooks/useVideo';
import { ROUTES, PAGE_SIZE_DEFAULT } from '@/lib/constants';
import type { VideoStatus } from '@/types/video';

export default function VideosPage() {
  const [status, setStatus] = useState<VideoStatus | 'all'>('all');
  const [page, setPage] = useState(1);
  const [selectMode, setSelectMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [confirmOpen, setConfirmOpen] = useState(false);

  const { data, isLoading, isError, refetch, isFetching } = useVideoList({
    page,
    page_size: PAGE_SIZE_DEFAULT,
    status: status === 'all' ? undefined : status,
  });

  const { mutate: deleteVideo } = useDeleteVideo();
  const { mutate: bulkDelete, isPending: isBulkDeleting } = useBulkDeleteVideos();

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE_DEFAULT) : 1;

  const handleSelect = (id: string, checked: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (checked) next.add(id);
      else next.delete(id);
      return next;
    });
  };

  const handleSelectAll = () => {
    const pageIds = data?.items.map((v) => v.id) ?? [];
    const allSelected = pageIds.every((id) => selectedIds.has(id));
    setSelectedIds(allSelected ? new Set() : new Set(pageIds));
  };

  const handleExitSelectMode = () => {
    setSelectMode(false);
    setSelectedIds(new Set());
  };

  const handleBulkDelete = () => {
    bulkDelete(Array.from(selectedIds), {
      onSuccess: () => {
        setConfirmOpen(false);
        handleExitSelectMode();
      },
    });
  };

  const pageIds = data?.items.map((v) => v.id) ?? [];
  const allPageSelected = pageIds.length > 0 && pageIds.every((id) => selectedIds.has(id));
  const somePageSelected = pageIds.some((id) => selectedIds.has(id));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Videos</h1>
          <p className="text-muted-foreground">
            {data ? `${data.total} video${data.total !== 1 ? 's' : ''}` : 'Loading…'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" onClick={() => refetch()} aria-label="Refresh" disabled={isFetching}>
            <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
          </Button>
          {!selectMode ? (
            <>
              <Button variant="outline" onClick={() => setSelectMode(true)}>
                <CheckSquare className="mr-2 h-4 w-4" />
                Select
              </Button>
              <Button asChild>
                <Link href={ROUTES.videoUpload}>
                  <Plus className="mr-2 h-4 w-4" />
                  Upload
                </Link>
              </Button>
            </>
          ) : (
            <>
              {selectedIds.size > 0 && (
                <Button
                  variant="destructive"
                  onClick={() => setConfirmOpen(true)}
                  disabled={isBulkDeleting}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete files ({selectedIds.size})
                </Button>
              )}
              <Button variant="outline" onClick={handleExitSelectMode}>
                <X className="mr-2 h-4 w-4" />
                Cancel
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Filters + select-all row */}
      <div className="flex items-center gap-3">
        <Select
          value={status}
          onValueChange={(v) => {
            setStatus(v as VideoStatus | 'all');
            setPage(1);
          }}
        >
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="processing">Processing</SelectItem>
            <SelectItem value="ready">Ready</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
            <SelectItem value="deleted">Deleted</SelectItem>
          </SelectContent>
        </Select>

        {selectMode && data && data.items.length > 0 && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Checkbox
              checked={allPageSelected}
              data-state={somePageSelected && !allPageSelected ? 'indeterminate' : undefined}
              onCheckedChange={handleSelectAll}
              aria-label="Select all on this page"
            />
            <span>
              {allPageSelected ? 'Deselect all' : 'Select all on page'}
              {selectedIds.size > 0 && ` (${selectedIds.size} selected)`}
            </span>
          </div>
        )}
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="aspect-video w-full rounded-lg" />
          ))}
        </div>
      ) : isError ? (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center">
          <p className="text-sm text-destructive">Failed to load videos.</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={() => refetch()}>
            Retry
          </Button>
        </div>
      ) : data?.items.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-12 text-center">
          <p className="text-muted-foreground">No videos found.</p>
          <Button asChild className="mt-4">
            <Link href={ROUTES.videoUpload}>Upload your first video</Link>
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {data?.items.map((video) => (
            <VideoCard
              key={video.id}
              video={video}
              onDelete={!selectMode ? deleteVideo : undefined}
              selectable={selectMode}
              selected={selectedIds.has(video.id)}
              onSelect={handleSelect}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Previous
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page} of {totalPages}
          </span>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            Next
          </Button>
        </div>
      )}

      {/* Confirmation dialog */}
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete {selectedIds.size} video file{selectedIds.size !== 1 ? 's' : ''}?</DialogTitle>
            <DialogDescription>
              The video file{selectedIds.size !== 1 ? 's' : ''} will be permanently removed from storage.
              Metadata, analysis results, and thumbnails will be retained so you don&apos;t need to reprocess.
              This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmOpen(false)} disabled={isBulkDeleting}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleBulkDelete} disabled={isBulkDeleting}>
              {isBulkDeleting ? 'Deleting…' : `Delete ${selectedIds.size} file${selectedIds.size !== 1 ? 's' : ''}`}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
