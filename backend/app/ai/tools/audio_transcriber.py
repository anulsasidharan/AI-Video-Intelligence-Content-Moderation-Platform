"""
T-02 Audio Transcriber Tool

Extracts audio from a video file using FFmpeg and transcribes it with the
OpenAI Whisper API.  Returns a structured transcript with per-segment timing.

Public API:
    result = await transcribe_audio(
        video_path="/tmp/video.mp4",
        language="en",
    )
    result.text        # str  full transcript
    result.segments    # list[TranscriptSegment]  [{start, end, text}, ...]
    result.language    # str  detected/provided language code
    result.error       # str | None  set on failure; pipeline continues
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from typing import Any

import structlog
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.config import settings

logger = structlog.get_logger(__name__)

_WHISPER_MODEL = "whisper-1"


# ── Output schemas ────────────────────────────────────────────────────────────


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class TranscriptResult(BaseModel):
    text: str = ""
    segments: list[TranscriptSegment] = Field(default_factory=list)
    language: str = "en"
    error: str | None = None


# ── Errors ────────────────────────────────────────────────────────────────────


class AudioTranscriptionError(RuntimeError):
    pass


# ── FFmpeg helper ─────────────────────────────────────────────────────────────


def _extract_audio_ffmpeg(video_path: str, output_wav: str) -> None:
    """
    Extract the audio track from a video file to a 16 kHz mono WAV.

    Raises:
        AudioTranscriptionError: If FFmpeg exits with a non-zero return code.
    """
    cmd = [
        "ffmpeg",
        "-y",  # overwrite output if it exists
        "-i",
        video_path,
        "-vn",  # drop video stream
        "-ar",
        "16000",  # 16 kHz — Whisper optimal sample rate
        "-ac",
        "1",  # mono
        "-f",
        "wav",
        output_wav,
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=120, check=False)
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace")
        raise AudioTranscriptionError(f"FFmpeg audio extraction failed: {stderr}")


# ── Public API ────────────────────────────────────────────────────────────────


async def transcribe_audio(
    video_path: str,
    *,
    language: str | None = None,
    _client: AsyncOpenAI | None = None,
) -> TranscriptResult:
    """
    Extract audio from a video file and transcribe it with OpenAI Whisper.

    The function is failure-safe: on any error it returns a TranscriptResult
    with an empty transcript and the error message rather than raising, so the
    wider AI pipeline can continue with degraded input.

    Args:
        video_path: Local file path to the video (gs:// URLs must be
                    downloaded first via FrameExtractor or StorageService).
        language:   ISO 639-1 language hint passed to Whisper (optional).
        _client:    AsyncOpenAI client override — use in tests to avoid live calls.

    Returns:
        TranscriptResult with text, per-segment timing, and detected language.
    """
    client = _client or AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    wav_fd, wav_path = tempfile.mkstemp(suffix=".wav")
    os.close(wav_fd)

    try:
        logger.info("audio_transcriber_ffmpeg_start", video_path=video_path)
        try:
            _extract_audio_ffmpeg(video_path, wav_path)
        except AudioTranscriptionError as exc:
            logger.warning("audio_transcriber_ffmpeg_failed", error=str(exc))
            return TranscriptResult(error=str(exc))

        logger.info("audio_transcriber_whisper_start", wav_path=wav_path)
        with open(wav_path, "rb") as audio_file:
            kwargs: dict[str, Any] = {
                "model": _WHISPER_MODEL,
                "file": audio_file,
                "response_format": "verbose_json",
            }
            if language:
                kwargs["language"] = language

            response = await client.audio.transcriptions.create(**kwargs)

        raw_segments: list[dict] = getattr(response, "segments", None) or []
        segments = [
            TranscriptSegment(
                start=float(seg.get("start", 0.0)),
                end=float(seg.get("end", 0.0)),
                text=seg.get("text", ""),
            )
            for seg in raw_segments
        ]

        detected_language: str = getattr(response, "language", None) or language or "en"

        logger.info(
            "audio_transcriber_done",
            text_len=len(response.text or ""),
            segment_count=len(segments),
            language=detected_language,
        )
        return TranscriptResult(
            text=response.text or "",
            segments=segments,
            language=detected_language,
        )

    except Exception as exc:
        logger.error("audio_transcriber_error", error=str(exc))
        return TranscriptResult(error=str(exc))
    finally:
        if os.path.exists(wav_path):
            os.unlink(wav_path)
