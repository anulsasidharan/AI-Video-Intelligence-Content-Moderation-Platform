'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import { ArrowLeft, AlertCircle, CheckCircle2, Download, Eye, Loader2 } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ROUTES } from '@/lib/constants';

// ── Types ──────────────────────────────────────────────────────────────────────

type ReportType = 'moderation_summary' | 'video_activity' | 'user_activity' | 'agent_performance' | 'violation_breakdown';
type Orientation = 'portrait' | 'landscape';

interface ColumnDef {
  key: string;
  label: string;
}

interface PreviewData {
  columns: string[];
  rows: Record<string, unknown>[];
  total: number;
  page: number;
  page_size: number;
  summary: Record<string, unknown>;
}

// ── Config ─────────────────────────────────────────────────────────────────────

const REPORT_TYPES: { value: ReportType; label: string; description: string }[] = [
  { value: 'moderation_summary', label: 'Moderation Summary', description: 'AI decisions, violations, and confidence scores per video.' },
  { value: 'video_activity', label: 'Video Activity', description: 'Upload history, processing status, file sizes, and ownership.' },
  { value: 'user_activity', label: 'User Activity', description: 'Registered users, roles, and account statuses.' },
  { value: 'agent_performance', label: 'Agent Performance', description: 'AI pipeline execution times, token usage, and error rates.' },
  { value: 'violation_breakdown', label: 'Violation Breakdown', description: 'Time-series breakdown of detected violations by category.' },
];

const COLUMNS_BY_TYPE: Record<ReportType, ColumnDef[]> = {
  moderation_summary: [
    { key: 'video_id', label: 'Video ID' },
    { key: 'video_title', label: 'Video Title' },
    { key: 'status', label: 'Status' },
    { key: 'overall_confidence', label: 'Confidence' },
    { key: 'violation_count', label: 'Violations' },
    { key: 'ai_model', label: 'AI Model' },
    { key: 'processing_time_ms', label: 'Processing Time (ms)' },
    { key: 'created_at', label: 'Created At' },
  ],
  video_activity: [
    { key: 'video_id', label: 'Video ID' },
    { key: 'title', label: 'Title' },
    { key: 'status', label: 'Status' },
    { key: 'source', label: 'Source' },
    { key: 'duration_seconds', label: 'Duration (s)' },
    { key: 'file_size_bytes', label: 'File Size (bytes)' },
    { key: 'owner_email', label: 'Owner Email' },
    { key: 'created_at', label: 'Created At' },
  ],
  user_activity: [
    { key: 'user_id', label: 'User ID' },
    { key: 'email', label: 'Email' },
    { key: 'name', label: 'Name' },
    { key: 'role', label: 'Role' },
    { key: 'is_active', label: 'Active' },
    { key: 'created_at', label: 'Created At' },
  ],
  agent_performance: [
    { key: 'trace_id', label: 'Trace ID' },
    { key: 'agent_name', label: 'Agent Name' },
    { key: 'status', label: 'Status' },
    { key: 'duration_ms', label: 'Duration (ms)' },
    { key: 'input_tokens', label: 'Input Tokens' },
    { key: 'output_tokens', label: 'Output Tokens' },
    { key: 'error_message', label: 'Error Message' },
    { key: 'created_at', label: 'Created At' },
  ],
  violation_breakdown: [
    { key: 'event_date', label: 'Date' },
    { key: 'category', label: 'Category' },
    { key: 'count', label: 'Count' },
    { key: 'avg_confidence', label: 'Avg Confidence' },
    { key: 'video_count', label: 'Videos Affected' },
  ],
};

const DATE_PRESETS = [
  { value: 'today', label: 'Today' },
  { value: 'last_7_days', label: 'Last 7 days' },
  { value: 'last_30_days', label: 'Last 30 days' },
  { value: 'last_90_days', label: 'Last 90 days' },
  { value: 'custom', label: 'Custom range' },
];

// ── Component ──────────────────────────────────────────────────────────────────

export default function ReportBuilderPage() {
  const router = useRouter();

  // Form state
  const [title, setTitle] = useState('');
  const [reportType, setReportType] = useState<ReportType>('moderation_summary');
  const [datePreset, setDatePreset] = useState<string>('last_30_days');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [orientation, setOrientation] = useState<Orientation>('portrait');
  const [selectedColumns, setSelectedColumns] = useState<Set<string>>(
    new Set(COLUMNS_BY_TYPE.moderation_summary.map((c) => c.key))
  );

  // Preview state
  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [activeTab, setActiveTab] = useState<'configure' | 'preview'>('configure');
  const [queuedJobId, setQueuedJobId] = useState<string | null>(null);

  const availableColumns = COLUMNS_BY_TYPE[reportType];

  function handleTypeChange(t: ReportType) {
    setReportType(t);
    setSelectedColumns(new Set(COLUMNS_BY_TYPE[t].map((c) => c.key)));
    setPreviewData(null);
    setQueuedJobId(null);
  }

  function toggleColumn(key: string) {
    setSelectedColumns((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  function buildFilters() {
    if (datePreset !== 'custom') {
      return { date_preset: datePreset };
    }
    return {
      ...(dateFrom && { date_from: dateFrom }),
      ...(dateTo && { date_to: dateTo }),
    };
  }

  // Preview mutation — apiClient.unwrapData already strips the { data: ... } envelope,
  // so the resolved value is PreviewData directly (not { data: PreviewData }).
  const previewMutation = useMutation<PreviewData, Error>({
    mutationFn: () =>
      apiClient.post<PreviewData>('/reports/preview', {
        report_type: reportType,
        filters: buildFilters(),
        columns: selectedColumns.size > 0 ? Array.from(selectedColumns) : null,
        page: 1,
        page_size: 50,
      }),
    onSuccess: (data) => {
      setPreviewData(data);
      setActiveTab('preview');
    },
  });

  // Generate mutation
  const generateMutation = useMutation<{ id: string }, Error>({
    mutationFn: () =>
      apiClient.post<{ id: string }>('/reports/generate', {
        title: title || `${REPORT_TYPES.find((t) => t.value === reportType)?.label} — ${new Date().toLocaleDateString()}`,
        report_type: reportType,
        filters: buildFilters(),
        columns: selectedColumns.size > 0 ? Array.from(selectedColumns) : null,
        orientation,
      }),
    onSuccess: (job) => {
      setQueuedJobId(job.id);
      setActiveTab('configure');
    },
  });

  const isValid = reportType && selectedColumns.size > 0;

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" asChild>
          <Link href={ROUTES.reports}>
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Report Builder</h1>
          <p className="text-sm text-muted-foreground">Configure and generate a PDF report.</p>
        </div>
      </div>

      {/* Error banners */}
      {previewMutation.isError && (
        <div className="flex items-center gap-2 rounded-md border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0" />
          Preview failed: {previewMutation.error?.message ?? 'Unknown error'}
        </div>
      )}
      {generateMutation.isError && (
        <div className="flex items-center gap-2 rounded-md border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0" />
          Report generation failed: {generateMutation.error?.message ?? 'Unknown error'}
        </div>
      )}
      {generateMutation.isSuccess && queuedJobId && (
        <div className="flex items-center justify-between gap-3 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            Report queued. You can monitor status in the Reports page.
          </div>
          <Button asChild size="sm" variant="outline">
            <Link href={ROUTES.reports}>View reports</Link>
          </Button>
        </div>
      )}

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
        <TabsList>
          <TabsTrigger value="configure">Configure</TabsTrigger>
          <TabsTrigger value="preview" disabled={!previewData}>
            Preview {previewData && <Badge variant="secondary" className="ml-1.5 text-xs">{previewData.total}</Badge>}
          </TabsTrigger>
        </TabsList>

        {/* ── Configure tab ────────────────────────────────────────────────── */}
        <TabsContent value="configure" className="space-y-6 mt-4">
          {/* Report title */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Report Title</CardTitle>
            </CardHeader>
            <CardContent>
              <Input
                placeholder="e.g. Weekly Moderation Summary — March 2026"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </CardContent>
          </Card>

          {/* Report type */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Report Type</CardTitle>
              <CardDescription>Choose what data this report should contain.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {REPORT_TYPES.map((rt) => (
                  <button
                    key={rt.value}
                    onClick={() => handleTypeChange(rt.value)}
                    className={`flex flex-col gap-1 rounded-lg border p-4 text-left transition-colors hover:border-primary ${
                      reportType === rt.value
                        ? 'border-primary bg-primary/5 ring-1 ring-primary'
                        : 'border-border'
                    }`}
                  >
                    <span className="font-medium text-sm">{rt.label}</span>
                    <span className="text-xs text-muted-foreground leading-relaxed">{rt.description}</span>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Filters */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Date Range</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {DATE_PRESETS.map((p) => (
                  <button
                    key={p.value}
                    onClick={() => setDatePreset(p.value)}
                    className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                      datePreset === p.value
                        ? 'border-primary bg-primary text-primary-foreground'
                        : 'border-border hover:border-primary'
                    }`}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
              {datePreset === 'custom' && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="date-from">From</Label>
                    <Input id="date-from" type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="date-to">To</Label>
                    <Input id="date-to" type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Columns */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Columns</CardTitle>
              <CardDescription>Choose which columns appear in the report.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {availableColumns.map((col) => (
                  <label key={col.key} className="flex items-center gap-2 cursor-pointer select-none">
                    <Checkbox
                      checked={selectedColumns.has(col.key)}
                      onCheckedChange={() => toggleColumn(col.key)}
                    />
                    <span className="text-sm">{col.label}</span>
                  </label>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Output options */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">PDF Options</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4">
                <Label>Orientation</Label>
                <div className="flex gap-2">
                  {(['portrait', 'landscape'] as const).map((o) => (
                    <button
                      key={o}
                      onClick={() => setOrientation(o)}
                      className={`rounded-md border px-3 py-1.5 text-sm capitalize transition-colors ${
                        orientation === o
                          ? 'border-primary bg-primary text-primary-foreground'
                          : 'border-border hover:border-primary'
                      }`}
                    >
                      {o}
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Action buttons */}
          <div className="flex gap-3">
            <Button
              variant="outline"
              disabled={!isValid || previewMutation.isPending}
              onClick={() => previewMutation.mutate()}
            >
              {previewMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
              ) : (
                <Eye className="h-4 w-4 mr-1.5" />
              )}
              Preview Data
            </Button>
            <Button
              disabled={!isValid || generateMutation.isPending}
              onClick={() => generateMutation.mutate()}
            >
              {generateMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
              ) : (
                <Download className="h-4 w-4 mr-1.5" />
              )}
              Generate PDF
            </Button>
          </div>
        </TabsContent>

        {/* ── Preview tab ──────────────────────────────────────────────────── */}
        <TabsContent value="preview" className="mt-4">
          {previewMutation.isPending && (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          )}

          {previewData && (
            <div className="space-y-4">
              {/* Summary stats */}
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                {Object.entries(previewData.summary)
                  .filter(([, v]) => typeof v === 'number')
                  .slice(0, 4)
                  .map(([key, val]) => (
                    <Card key={key} className="py-3">
                      <CardContent className="px-4">
                        <p className="text-xl font-bold">{typeof val === 'number' ? val.toLocaleString() : String(val)}</p>
                        <p className="text-xs text-muted-foreground mt-0.5">{key.replace(/_/g, ' ')}</p>
                      </CardContent>
                    </Card>
                  ))}
              </div>

              {/* Data table */}
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">
                      Preview — {previewData.rows.length} of {previewData.total} rows
                    </CardTitle>
                    <Button
                      size="sm"
                      disabled={!isValid || generateMutation.isPending}
                      onClick={() => generateMutation.mutate()}
                    >
                      {generateMutation.isPending ? (
                        <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
                      ) : (
                        <Download className="h-4 w-4 mr-1.5" />
                      )}
                      Generate PDF
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="p-0 overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {previewData.columns.map((col) => (
                          <TableHead key={col} className="whitespace-nowrap">
                            {col.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                          </TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {previewData.rows.map((row, i) => (
                        <TableRow key={i}>
                          {previewData.columns.map((col) => (
                            <TableCell key={col} className="text-sm whitespace-nowrap max-w-[200px] truncate">
                              {row[col] != null ? String(row[col]) : '—'}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
