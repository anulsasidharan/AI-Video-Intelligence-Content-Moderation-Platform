'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, CheckCircle2, Link2, Upload } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { UploadDropzone } from '@/components/video/UploadDropzone';
import { useBulkUploadVideo, checkDuplicates, useAnalyzeUrl } from '@/hooks/useVideo';
import { ROUTES } from '@/lib/constants';
import type { UploadFile } from '@/types/video';

export default function UploadPage() {
  const router = useRouter();

  // ── File upload state ──────────────────────────────────────────────────────
  const [files, setFiles] = useState<UploadFile[]>([]);
  const { uploadAll, isUploading } = useBulkUploadVideo();

  const doneCount = files.filter((f) => f.status === 'done').length;
  const errorCount = files.filter((f) => f.status === 'error').length;
  const pendingCount = files.filter((f) => f.status === 'pending').length;
  const allDone = files.length > 0 && doneCount + errorCount === files.length;
  const uploadableCount = files.filter(
    (f) => f.status === 'pending' || f.status === 'error'
  ).length;

  const handleFilesAdded = async (newFiles: UploadFile[]) => {
    setFiles((prev) => {
      const existingKeys = new Set(prev.map((f) => `${f.file.name}-${f.file.size}`));
      return [
        ...prev,
        ...newFiles.filter((f) => !existingKeys.has(`${f.file.name}-${f.file.size}`)),
      ];
    });

    try {
      const duplicateKeys = await checkDuplicates(newFiles);
      if (duplicateKeys.size === 0) return;
      const duplicateNames = newFiles
        .filter((f) => duplicateKeys.has(`${f.file.name}-${f.file.size}`))
        .map((f) => f.file.name);
      setFiles((prev) =>
        prev.filter((f) => !duplicateKeys.has(`${f.file.name}-${f.file.size}`))
      );
      toast.warning(
        duplicateNames.length === 1
          ? `"${duplicateNames[0]}" already exists — skipped`
          : `${duplicateNames.length} files already exist and were skipped:\n${duplicateNames.join(', ')}`
      );
    } catch {
      // non-fatal
    }
  };

  const handleFileRemove = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const handleUpload = async () => {
    if (files.length === 0 || isUploading) return;
    const onUpdate = (
      id: string,
      patch: Partial<Pick<UploadFile, 'status' | 'progress' | 'error'>>
    ) => {
      setFiles((prev) => prev.map((f) => (f.id === id ? { ...f, ...patch } : f)));
    };
    await uploadAll(files, onUpdate);
  };

  const fileButtonLabel = isUploading
    ? `Uploading (${doneCount}/${files.length})…`
    : uploadableCount > 0
    ? `Upload ${uploadableCount} video${uploadableCount > 1 ? 's' : ''}`
    : 'Upload & process';

  // ── URL analysis state ─────────────────────────────────────────────────────
  const [url, setUrl] = useState('');
  const [urlTitle, setUrlTitle] = useState('');
  const { mutate: analyzeUrl, isPending: isAnalyzing } = useAnalyzeUrl();

  const handleAnalyzeUrl = () => {
    if (!url.trim()) return;
    analyzeUrl(
      { url: url.trim(), title: urlTitle.trim() || undefined },
      {
        onSuccess: () => {
          router.push(ROUTES.videos);
        },
      }
    );
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => router.back()} aria-label="Go back">
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Add Video</h1>
          <p className="text-muted-foreground">
            Upload files or paste a web URL for AI content moderation
          </p>
        </div>
      </div>

      <Tabs defaultValue="file">
        <TabsList className="w-full">
          <TabsTrigger value="file" className="flex-1">
            <Upload className="mr-2 h-4 w-4" />
            File Upload
          </TabsTrigger>
          <TabsTrigger value="url" className="flex-1">
            <Link2 className="mr-2 h-4 w-4" />
            Web URL
          </TabsTrigger>
        </TabsList>

        {/* ── File upload tab ─────────────────────────────────────────────── */}
        <TabsContent value="file">
          <Card>
            <CardHeader>
              <CardTitle>Select files</CardTitle>
              <CardDescription>
                Supported formats: MP4, WebM, MOV, AVI, MKV — up to 5 GB per file
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <UploadDropzone
                files={files}
                onFilesAdded={handleFilesAdded}
                onFileRemove={handleFileRemove}
                disabled={isUploading}
              />

              {allDone && (
                <div className="flex items-center gap-2 rounded-md bg-green-50 px-4 py-3 text-sm text-green-700 dark:bg-green-950/30 dark:text-green-400">
                  <CheckCircle2 className="h-4 w-4 shrink-0" />
                  <span>
                    {doneCount} video{doneCount !== 1 ? 's' : ''} uploaded
                    {errorCount > 0 ? `, ${errorCount} failed` : ''}
                  </span>
                </div>
              )}

              <div className="flex items-center justify-between gap-2">
                <div className="text-sm text-muted-foreground">
                  {files.length > 0 && !allDone && !isUploading && (
                    <span>{pendingCount} file{pendingCount !== 1 ? 's' : ''} ready</span>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={() => router.back()} disabled={isUploading}>
                    Cancel
                  </Button>
                  {allDone ? (
                    <Button onClick={() => router.push(ROUTES.videos)}>Go to Videos</Button>
                  ) : (
                    <Button
                      onClick={handleUpload}
                      disabled={uploadableCount === 0 || isUploading}
                    >
                      {fileButtonLabel}
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── URL tab ─────────────────────────────────────────────────────── */}
        <TabsContent value="url">
          <Card>
            <CardHeader>
              <CardTitle>Analyze a web video</CardTitle>
              <CardDescription>
                Paste a YouTube, Vimeo, or any supported video URL. The video will be
                downloaded, analyzed, and the file stored for AI moderation.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="video-url">Video URL</Label>
                <Input
                  id="video-url"
                  type="url"
                  placeholder="https://www.youtube.com/watch?v=..."
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  disabled={isAnalyzing}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="url-title">
                  Title{' '}
                  <span className="text-muted-foreground font-normal">(optional — auto-detected if blank)</span>
                </Label>
                <Input
                  id="url-title"
                  placeholder="Leave blank to use the video's own title"
                  value={urlTitle}
                  onChange={(e) => setUrlTitle(e.target.value)}
                  disabled={isAnalyzing}
                />
              </div>

              <div className="rounded-md border bg-muted/40 px-4 py-3 text-xs text-muted-foreground space-y-1">
                <p className="font-medium text-foreground">Supported platforms include:</p>
                <p>YouTube · Vimeo · Twitter/X · TikTok · Facebook · Dailymotion · and 1000+ more via yt-dlp</p>
              </div>

              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => router.back()} disabled={isAnalyzing}>
                  Cancel
                </Button>
                <Button
                  onClick={handleAnalyzeUrl}
                  disabled={!url.trim() || isAnalyzing}
                >
                  {isAnalyzing ? 'Submitting…' : 'Analyze URL'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
