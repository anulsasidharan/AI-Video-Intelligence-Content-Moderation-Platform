'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { format, formatDistanceToNow } from 'date-fns';
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Download,
  FileText,
  Loader2,
  Plus,
  RefreshCw,
  Trash2,
} from 'lucide-react';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api';
import { getBrowserApiV1Root } from '@/lib/apiOrigin';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ROUTES } from '@/lib/constants';

// ── Types ──────────────────────────────────────────────────────────────────────

interface ReportJob {
  id: string;
  title: string;
  report_type: string;
  status: 'pending' | 'generating' | 'ready' | 'failed';
  filters: Record<string, unknown> | null;
  columns: string[] | null;
  orientation: string;
  s3_key: string | null;
  file_size_bytes: number | null;
  row_count: number | null;
  error_message: string | null;
  celery_task_id: string | null;
  template_id: string | null;
  generated_by: string;
  created_at: string;
  updated_at: string;
}

interface JobsResponse {
  items: ReportJob[];
  total: number;
  page: number;
  page_size: number;
}

// ── Helpers ────────────────────────────────────────────────────────────────────

const REPORT_TYPE_LABELS: Record<string, string> = {
  moderation_summary: 'Moderation Summary',
  video_activity: 'Video Activity',
  user_activity: 'User Activity',
  agent_performance: 'Agent Performance',
  violation_breakdown: 'Violation Breakdown',
};

const STATUS_CONFIG = {
  ready: { label: 'Ready', icon: CheckCircle2, variant: 'default' as const, className: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
  generating: { label: 'Generating…', icon: Loader2, variant: 'secondary' as const, className: 'bg-blue-100 text-blue-700 border-blue-200' },
  pending: { label: 'Pending', icon: Clock, variant: 'outline' as const, className: 'bg-slate-100 text-slate-600 border-slate-200' },
  failed: { label: 'Failed', icon: AlertCircle, variant: 'destructive' as const, className: 'bg-red-100 text-red-700 border-red-200' },
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ── Component ──────────────────────────────────────────────────────────────────

export default function ReportsPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [page, setPage] = useState(1);

  const { data, isLoading, isFetching, isError, error, refetch } = useQuery<JobsResponse>({
    queryKey: ['report-jobs', statusFilter, page],
    queryFn: () =>
      // Trailing slash matches FastAPI route and avoids 307 → http:// mixed-content
      // when reverse proxies do not rewrite Location (see FORWARDED_ALLOW_IPS).
      apiClient.get<JobsResponse>(`/reports/`, {
        params: {
          page,
          page_size: 20,
          ...(statusFilter !== 'all' && { status: statusFilter }),
        },
      }),
    refetchInterval: (query) => {
      // Poll every 5s if any job is in generating/pending state
      const jobs = query.state.data?.items ?? [];
      const hasActive = jobs.some((j: ReportJob) => j.status === 'generating' || j.status === 'pending');
      return hasActive ? 5000 : false;
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (jobId: string) => apiClient.delete(`/reports/${jobId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['report-jobs'] }),
  });

  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const handleDownload = async (job: ReportJob) => {
    if (downloadingId) return;
    setDownloadingId(job.id);
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const url = `${getBrowserApiV1Root()}/reports/${job.id}/download`;
      const res = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) {
        let msg = `Download failed (${res.status})`;
        try { const j = await res.json(); if (j?.detail) msg = j.detail; } catch { /* ignore */ }
        toast.error(msg);
        return;
      }
      const blob = await res.blob();
      const filename = job.title.replace(/[^a-z0-9_\-. ]/gi, '_') + '.pdf';
      const href = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = href;
      a.download = filename;
      a.rel = 'noopener';
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(href);
      toast.success('Report downloaded');
    } catch {
      toast.error('Could not download the report. Please try again.');
    } finally {
      setDownloadingId(null);
    }
  };

  const jobs = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / 20);

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Reports</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Generate, download, and manage PDF reports for admin use.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCw className={`h-4 w-4 mr-1.5 ${isFetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button asChild size="sm">
            <Link href={ROUTES.reportBuilder}>
              <Plus className="h-4 w-4 mr-1.5" />
              New Report
            </Link>
          </Button>
        </div>
      </div>

      {/* Summary stat cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {(['ready', 'generating', 'pending', 'failed'] as const).map((s) => {
          const count = jobs.filter((j) => j.status === s).length;
          const cfg = STATUS_CONFIG[s];
          const Icon = cfg.icon;
          return (
            <Card key={s} className="py-4">
              <CardContent className="flex items-center gap-3 px-4">
                <Icon className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-2xl font-bold">{count}</p>
                  <p className="text-xs text-muted-foreground">{cfg.label}</p>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Jobs table */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Report History</CardTitle>
              <CardDescription>{total} total report(s)</CardDescription>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="All statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                <SelectItem value="ready">Ready</SelectItem>
                <SelectItem value="generating">Generating</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : isError ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3">
              <AlertCircle className="h-10 w-10 text-destructive opacity-60" />
              <p className="text-sm font-medium text-destructive">Failed to load reports</p>
              <p className="text-xs text-muted-foreground">
                {(error as Error)?.message ?? 'An unexpected error occurred. Please try again.'}
              </p>
              <Button variant="outline" size="sm" onClick={() => refetch()}>
                <RefreshCw className="h-4 w-4 mr-1.5" />
                Retry
              </Button>
            </div>
          ) : jobs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-3">
              <FileText className="h-10 w-10 opacity-30" />
              <p className="text-sm">No reports yet. Create one to get started.</p>
              <Button asChild size="sm" variant="outline">
                <Link href={ROUTES.reportBuilder}>
                  <Plus className="h-4 w-4 mr-1.5" />
                  New Report
                </Link>
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Rows</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Generated</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobs.map((job) => {
                  const cfg = STATUS_CONFIG[job.status];
                  const Icon = cfg.icon;
                  return (
                    <TableRow key={job.id}>
                      <TableCell className="font-medium max-w-[220px] truncate">
                        {job.title}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {REPORT_TYPE_LABELS[job.report_type] ?? job.report_type}
                      </TableCell>
                      <TableCell>
                        <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${cfg.className}`}>
                          <Icon className={`h-3 w-3 ${job.status === 'generating' ? 'animate-spin' : ''}`} />
                          {cfg.label}
                        </span>
                      </TableCell>
                      <TableCell className="text-sm">
                        {job.row_count != null ? job.row_count.toLocaleString() : '—'}
                      </TableCell>
                      <TableCell className="text-sm">
                        {job.file_size_bytes != null ? formatBytes(job.file_size_bytes) : '—'}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          {job.status === 'ready' && (
                            <Button
                              variant="ghost"
                              size="icon"
                              title="Download PDF"
                              disabled={downloadingId === job.id}
                              onClick={() => handleDownload(job)}
                            >
                              {downloadingId === job.id ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Download className="h-4 w-4" />
                              )}
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="icon"
                            title="Delete"
                            className="text-destructive hover:text-destructive"
                            disabled={deleteMutation.isPending}
                            onClick={() => deleteMutation.mutate(job.id)}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-end gap-2">
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
    </div>
  );
}
