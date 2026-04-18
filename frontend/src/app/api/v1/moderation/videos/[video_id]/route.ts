import { NextResponse } from 'next/server';

export async function GET(_req: Request, { params }: { params: { video_id: string } }) {
  return NextResponse.json({
    data: {
      id: 'q-mock-' + params.video_id,
      video_id: params.video_id,
      status: 'flagged',
      priority: 1,
      overall_confidence: 0.942,
      ai_summary:
        'This video contains high-confidence depictions of physical violence and threatening language detected via audio transcription. A weapon was also identified in multiple frames. Immediate quarantine is recommended per Enterprise Content Policy v2.3.',
      ai_model: 'gpt-4o',
      violations: [
        {
          category: 'violence',
          severity: 'high',
          confidence: 0.91,
          timestamp: 42,
          description: 'Physical altercation detected across 14 consecutive frames. Bounding boxes: person (0.97), bat/weapon (0.88).',
          frame_index: 294,
        },
        {
          category: 'hate_speech',
          severity: 'high',
          confidence: 0.96,
          timestamp: 77,
          description: 'Threatening language detected in audio: "I\'m going to hurt you." Speaker A, 00:42–00:48. Whisper confidence 96%.',
          frame_index: 0,
        },
        {
          category: 'drugs',
          severity: 'medium',
          confidence: 0.88,
          timestamp: 125,
          description: 'Weapon (bat/blunt object) visible in 7 frames at 02:05. Object detection model confidence 88%.',
          frame_index: 875,
        },
      ],
      report: {
        violations: [
          {
            id: 'v-mock-1',
            category: 'violence',
            timestamp_seconds: 42,
            confidence: 0.91,
            snippet: 'Detected physical altercation in frame sequence 24–31. Objects: person (0.97), bat (0.88).',
            frame_url: null,
          },
          {
            id: 'v-mock-2',
            category: 'hate_symbols',
            timestamp_seconds: 77,
            confidence: 0.96,
            snippet: 'Threatening language in audio at 00:42–00:48. Speaker A: "I\'m going to hurt you."',
            frame_url: null,
          },
          {
            id: 'v-mock-3',
            category: 'other',
            timestamp_seconds: 125,
            confidence: 0.88,
            snippet: 'Blunt weapon visible in 7 frames across 02:05–02:09.',
            frame_url: null,
          },
        ],
        recommended_action: 'reject',
        summary:
          'High-confidence multi-category violation. Violence (91%), Threatening Language (96%), Weapon Detection (88%). Policy: Enterprise Content Policy v2.3. Processing time: 8.5s.',
        processed_at: new Date().toISOString(),
      },
      agent_log: [
        { ts: '00:00.312', agent: 'OrchestratorAgent', message: 'Dispatching 5 specialist agents for video analysis', level: 'info' },
        { ts: '00:00.418', agent: 'ContentAnalyzer', message: 'Sampling 84 frames @ 7fps using FFmpeg', level: 'info' },
        { ts: '00:01.204', agent: 'AudioTranscriber', message: 'Whisper-large-v3 loaded — starting transcription', level: 'info' },
        { ts: '00:02.891', agent: 'ContentAnalyzer', message: 'Frame 00:42 — VIOLENCE: 0.91 ⚠ bounding boxes: person (0.97), bat (0.88)', level: 'warn' },
        { ts: '00:03.112', agent: 'SafetyChecker', message: 'Policy match: violence_threshold (0.91 > 0.85) — FLAGGED', level: 'error' },
        { ts: '00:04.780', agent: 'MetadataExtractor', message: 'Entities extracted: [weapon, person, outdoor, daytime]', level: 'info' },
        { ts: '00:05.340', agent: 'SceneClassifier', message: 'Scene: confrontation · outdoor · daytime — Category: violence', level: 'info' },
        { ts: '00:05.901', agent: 'AudioTranscriber', message: 'Threatening language at 00:42–00:48: "I\'m going to hurt you." (confidence 0.96)', level: 'error' },
        { ts: '00:06.001', agent: 'OCRTool', message: 'Text overlay detected: "EXIT" at frame 00:51 — benign', level: 'info' },
        { ts: '00:06.890', agent: 'ContentAnalyzer', message: 'Frame 02:05 — weapon visible: bat/blunt object (0.88)', level: 'warn' },
        { ts: '00:07.230', agent: 'ReportGenerator', message: 'Compiling moderation report — 3 violations, 2 HIGH, 1 MEDIUM', level: 'info' },
        { ts: '00:08.544', agent: 'OrchestratorAgent', message: '✅ Analysis complete — decision: FLAGGED · confidence 94.2%', level: 'success' },
      ],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  });
}
