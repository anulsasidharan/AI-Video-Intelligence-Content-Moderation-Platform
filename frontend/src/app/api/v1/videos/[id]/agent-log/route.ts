import { NextResponse } from 'next/server';

const FULL_LOG = [
  { ts: '00:00.312', agent: 'OrchestratorAgent', message: 'Dispatching 5 specialist agents for video analysis', level: 'info' },
  { ts: '00:00.418', agent: 'ContentAnalyzer', message: 'Sampling 84 frames @ 7fps using FFmpeg', level: 'info' },
  { ts: '00:01.204', agent: 'AudioTranscriber', message: 'Whisper-large-v3 loaded — starting transcription', level: 'info' },
  { ts: '00:02.891', agent: 'ContentAnalyzer', message: 'Frame 00:42 — VIOLENCE: 0.91 ⚠ bounding boxes: person (0.97), bat (0.88)', level: 'warn' },
  { ts: '00:03.112', agent: 'SafetyChecker', message: 'Policy match: violence_threshold (0.91 > 0.85) — FLAGGED', level: 'error' },
  { ts: '00:04.780', agent: 'MetadataExtractor', message: 'Entities extracted: [weapon, person, outdoor, daytime]', level: 'info' },
  { ts: '00:05.340', agent: 'SceneClassifier', message: 'Scene: confrontation · outdoor · daytime', level: 'info' },
  { ts: '00:05.901', agent: 'AudioTranscriber', message: 'Threatening language at 00:42–00:48 — confidence 0.96', level: 'error' },
  { ts: '00:06.001', agent: 'OCRTool', message: 'Text overlay detected: "EXIT" at frame 00:51 — benign', level: 'info' },
  { ts: '00:06.890', agent: 'ContentAnalyzer', message: 'Frame 02:05 — weapon visible: bat/blunt object (0.88)', level: 'warn' },
  { ts: '00:07.230', agent: 'ReportGenerator', message: 'Compiling moderation report — 3 violations, 2 HIGH, 1 MEDIUM', level: 'info' },
  { ts: '00:08.544', agent: 'OrchestratorAgent', message: '✅ Analysis complete — decision: FLAGGED · confidence 94.2%', level: 'success' },
];

export async function GET(_req: Request, { params }: { params: { id: string } }) {
  void params;
  return NextResponse.json({ data: FULL_LOG });
}
