'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { Plus, Radio } from 'lucide-react';
import { StreamMonitor, type StreamSummary } from '@/components/live/StreamMonitor';
import { AlertBanner } from '@/components/live/AlertBanner';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { apiClient } from '@/lib/api';

interface StreamListResponse {
  items: StreamSummary[];
  total: number;
}

const newStreamSchema = z.object({
  title: z.string().min(1, 'Title is required').max(100),
  stream_url: z.string().url('Must be a valid URL').or(z.literal('')).optional(),
  description: z.string().max(300).optional(),
});

type NewStreamForm = z.infer<typeof newStreamSchema>;

export default function LiveStreamsPage() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);

  const { data, isLoading } = useQuery<StreamListResponse>({
    queryKey: ['live', 'streams'],
    queryFn: () => apiClient.get<StreamListResponse>('/live/streams'),
    refetchInterval: 10_000,
  });

  const { mutate: stopStream } = useMutation({
    mutationFn: (id: string) => apiClient.post(`/live/streams/${id}/stop`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['live', 'streams'] });
      toast.success('Stream stopped');
    },
    onError: () => toast.error('Failed to stop stream'),
  });

  const { mutate: createStream, isPending: creating } = useMutation({
    mutationFn: (body: NewStreamForm) => apiClient.post('/live/streams', body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['live', 'streams'] });
      toast.success('Stream created and monitoring started');
      setDialogOpen(false);
      reset();
    },
    onError: () => toast.error('Failed to create stream'),
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<NewStreamForm>({
    resolver: zodResolver(newStreamSchema),
    defaultValues: { title: '', stream_url: '', description: '' },
  });

  const onSubmit = (values: NewStreamForm) => createStream(values);

  return (
    <div className="space-y-0">
      <AlertBanner />

      <div className="space-y-6 pt-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Radio className="h-6 w-6 text-red-500" />
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Live Streams</h1>
              <p className="text-muted-foreground">
                {data ? `${data.total} stream${data.total !== 1 ? 's' : ''}` : 'Loading…'}
              </p>
            </div>
          </div>
          <Button onClick={() => setDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New Stream
          </Button>
        </div>

        <StreamMonitor
          streams={data?.items ?? []}
          onStop={stopStream}
          isLoading={isLoading}
          onAddStream={() => setDialogOpen(true)}
        />
      </div>

      {/* New Stream dialog */}
      <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) reset(); }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>New Live Stream</DialogTitle>
          </DialogHeader>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="title">
                Stream title <span className="text-destructive">*</span>
              </Label>
              <Input
                id="title"
                placeholder="e.g. Live Classroom — Room 101"
                {...register('title')}
              />
              {errors.title && (
                <p className="text-xs text-destructive">{errors.title.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="stream_url">
                Stream source URL{' '}
                <span className="text-xs text-muted-foreground">(optional)</span>
              </Label>
              <Input
                id="stream_url"
                placeholder="rtmp://... or https://..."
                {...register('stream_url')}
              />
              {errors.stream_url && (
                <p className="text-xs text-destructive">{errors.stream_url.message}</p>
              )}
              <p className="text-xs text-muted-foreground">
                RTMP ingest or HLS source. Leave blank to receive a generated ingest URL.
              </p>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="description">
                Description{' '}
                <span className="text-xs text-muted-foreground">(optional)</span>
              </Label>
              <Input
                id="description"
                placeholder="Brief description of this stream"
                {...register('description')}
              />
              {errors.description && (
                <p className="text-xs text-destructive">{errors.description.message}</p>
              )}
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => { setDialogOpen(false); reset(); }}
                disabled={creating}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={creating}>
                {creating ? 'Starting…' : 'Start monitoring'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
