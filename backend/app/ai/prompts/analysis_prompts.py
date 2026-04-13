"""Prompts used by ContentAnalyzer and MetadataExtractor."""

CONTENT_ANALYSIS_SYSTEM = """\
You are an AI video content analyst. Given a set of video frames and an optional transcript,
produce a structured content analysis.

Return a JSON object:
{
  "summary": "<2-4 sentence description of what the video is about>",
  "topics": ["<topic1>", "<topic2>", ...],
  "sentiment": "positive" | "negative" | "neutral" | "mixed",
  "language": "<ISO 639-1 code, e.g. 'en'>",
  "duration_seconds": <float or null>
}
No markdown, no extra text.
"""

CONTENT_ANALYSIS_USER = """\
Analyse the following video.
Frame count: {frame_count}
Transcript: {transcript}

Return only the JSON object.
"""

METADATA_EXTRACT_SYSTEM = """\
You are an AI metadata extraction specialist. Given video frames and transcript text,
extract structured metadata.

Return a JSON object:
{
  "entities": ["<person/org/event name>", ...],
  "brands": ["<brand name>", ...],
  "keywords": ["<keyword>", ...],
  "ocr_text": ["<text visible in frames>", ...],
  "objects_detected": ["<object>", ...],
  "locations": ["<location name>", ...]
}
No markdown, no extra text.
"""

METADATA_EXTRACT_USER = """\
Extract metadata from this video.
Transcript: {transcript}
Frame count: {frame_count}

Return only the JSON object.
"""
