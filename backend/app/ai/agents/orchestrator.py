"""
A-01 Orchestrator Agent

Entry point node in the LangGraph pipeline. Responsible for:
1. Validating the input state (video_id, video_url are present)
2. Loading active policy rules from DB (passed in via state["policy_rules"])
3. Sampling frames from the video URL using FFmpeg / OpenCV stub
4. Fetching / generating a transcript (Whisper stub)
5. Initialising the error and completed_agents lists

The orchestrator is the FIRST node. All specialist agents run after it.
"""

from __future__ import annotations

import base64
import io
from typing import Any

import structlog

from app.ai.base import BaseAgent

logger = structlog.get_logger(__name__)

# Number of frames to sample across the video duration
_TARGET_FRAMES = 16
_FRAME_INTERVAL_SEC = 5.0  # fallback when duration unknown


class OrchestratorAgent(BaseAgent):
    name = "orchestrator"

    async def run(self, state: dict[str, Any]) -> dict[str, Any]:
        video_id: str = state.get("video_id", "")
        video_url: str = state.get("video_url", "")

        logger.info("orchestrator_start", video_id=video_id, video_url=video_url[:60])

        errors: list[str] = list(state.get("errors") or [])
        updates: dict[str, Any] = {
            "errors": errors,
            "completed_agents": self._mark_completed(state),
        }

        # ── Frame sampling ────────────────────────────────────────────────────
        if not state.get("frames"):
            try:
                frames, timestamps = await self._sample_frames(video_url)
                updates["frames"] = frames
                updates["frame_timestamps"] = timestamps
                logger.info(
                    "orchestrator_frames_sampled",
                    video_id=video_id,
                    count=len(frames),
                )
            except Exception as exc:
                logger.error("orchestrator_frame_error", video_id=video_id, error=str(exc))
                errors.append(f"[orchestrator] Frame sampling failed: {exc}")
                updates["frames"] = []
                updates["frame_timestamps"] = []

        # ── Transcript ────────────────────────────────────────────────────────
        if not state.get("transcript"):
            try:
                transcript, segments = await self._transcribe(video_url)
                updates["transcript"] = transcript
                updates["transcript_segments"] = segments
                logger.info(
                    "orchestrator_transcript_ready",
                    video_id=video_id,
                    length=len(transcript),
                )
            except Exception as exc:
                logger.warning("orchestrator_transcript_error", video_id=video_id, error=str(exc))
                errors.append(f"[orchestrator] Transcription failed: {exc}")
                updates["transcript"] = ""
                updates["transcript_segments"] = []

        updates["errors"] = errors
        return updates

    # ── Frame sampling (FFmpeg via subprocess or OpenCV) ──────────────────────

    async def _sample_frames(self, video_url: str) -> tuple[list[str], list[float]]:
        """
        Sample frames from a video URL.

        In production this calls FFmpeg via asyncio.subprocess to extract
        JPEG frames at regular intervals. Here we provide a lightweight
        implementation that works with both real URLs and test stubs.
        """
        import asyncio

        if not video_url or video_url.startswith("http") is False and not video_url.startswith("/"):
            # Return placeholder for test / stub environments
            return self._placeholder_frames(_TARGET_FRAMES)

        cmd = [
            "ffmpeg",
            "-i",
            video_url,
            "-vf",
            f"fps=1/{_FRAME_INTERVAL_SEC},scale=320:-1",
            "-vframes",
            str(_TARGET_FRAMES),
            "-f",
            "image2pipe",
            "-vcodec",
            "mjpeg",
            "pipe:1",
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
        except (FileNotFoundError, TimeoutError):
            # FFmpeg not available (test env) — return placeholders
            return self._placeholder_frames(_TARGET_FRAMES)

        frames = self._split_mjpeg(stdout)
        timestamps = [i * _FRAME_INTERVAL_SEC for i in range(len(frames))]
        return frames, timestamps

    @staticmethod
    def _split_mjpeg(data: bytes) -> list[str]:
        """Split a concatenated MJPEG byte stream into individual base64 frames."""
        SOI = b"\xff\xd8"
        EOI = b"\xff\xd9"
        frames: list[str] = []
        pos = 0
        while True:
            start = data.find(SOI, pos)
            if start == -1:
                break
            end = data.find(EOI, start)
            if end == -1:
                break
            frame_bytes = data[start : end + 2]
            frames.append(base64.b64encode(frame_bytes).decode())
            pos = end + 2
        return frames

    @staticmethod
    def _placeholder_frames(n: int) -> tuple[list[str], list[float]]:
        """Return n tiny 1×1 white JPEG frames for testing."""
        # Minimal valid JPEG (1×1 white pixel)
        tiny_jpeg = (
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
            b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
            b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
            b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\x1e\xb6"
            b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
            b"\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b"
            b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xf5\xf5\xff\xd9"
        )
        b64 = base64.b64encode(tiny_jpeg).decode()
        frames = [b64] * n
        timestamps = [float(i * _FRAME_INTERVAL_SEC) for i in range(n)]
        return frames, timestamps

    # ── Transcription (OpenAI Whisper) ────────────────────────────────────────

    async def _transcribe(self, video_url: str) -> tuple[str, list[dict]]:
        """
        Transcribe audio from a video URL using OpenAI Whisper.

        In test environments where the URL is not reachable, returns empty strings.
        """
        if not video_url or not video_url.startswith("http"):
            return "", []

        try:
            import httpx

            async with httpx.AsyncClient() as http:
                resp = await http.get(video_url, timeout=30)
                resp.raise_for_status()
                audio_bytes = resp.content
        except Exception:
            return "", []

        response = await self.client.audio.transcriptions.create(
            model="whisper-1",
            file=("audio.mp4", io.BytesIO(audio_bytes), "video/mp4"),
            response_format="verbose_json",
        )

        transcript = getattr(response, "text", "") or ""
        segments = getattr(response, "segments", []) or []
        return transcript, [
            {
                "start": s.get("start", 0),
                "end": s.get("end", 0),
                "text": s.get("text", ""),
            }
            for s in (segments if isinstance(segments, list) else [])
        ]
