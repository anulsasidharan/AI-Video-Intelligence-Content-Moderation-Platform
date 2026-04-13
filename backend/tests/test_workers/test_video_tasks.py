"""Tests for W-02 — video_tasks (all external I/O mocked)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

# ── Helpers ────────────────────────────────────────────────────────────────────

_VIDEO_ID = str(uuid.uuid4())
_S3_KEY = "videos/test.mp4"


# Minimal ModerationReport-like object returned by run_video_analysis mock
def _fake_report():
    report = MagicMock()
    report.decision.value = "approved"
    report.confidence = 0.92
    report.violations = []
    report.content_summary = "Test video."
    report.model_dump.return_value = {
        "video_id": _VIDEO_ID,
        "decision": "approved",
        "confidence": 0.92,
        "violations": [],
        "content_summary": "Test video.",
    }
    return report


# ── extract_frames_task ────────────────────────────────────────────────────────


class TestExtractFramesTask:
    @patch("app.workers.video_tasks.extract_frames")
    def test_happy_path_returns_frame_dict(self, mock_extract):
        mock_result = MagicMock()
        mock_result.frames = ["b64frame1", "b64frame2"]
        mock_result.timestamps = [0.0, 2.0]
        mock_result.fps = 25.0
        mock_result.duration = 10.0
        mock_result.frame_count_extracted = 2
        mock_extract.return_value = mock_result

        from app.workers.video_tasks import extract_frames_task

        result = extract_frames_task(_VIDEO_ID, _S3_KEY)

        assert result["frames"] == ["b64frame1", "b64frame2"]
        assert result["fps"] == 25.0
        assert result["duration"] == 10.0
        mock_extract.assert_called_once()

    @patch("app.workers.video_tasks.extract_frames")
    def test_extraction_error_triggers_retry(self, mock_extract):
        from app.ai.tools.frame_extractor import FrameExtractionError
        from app.workers.video_tasks import extract_frames_task

        mock_extract.side_effect = FrameExtractionError("cannot open video")

        with pytest.raises(Exception):  # noqa: B017 — retry wraps varied error types
            extract_frames_task.apply(args=[_VIDEO_ID, _S3_KEY]).get(propagate=True)


# ── transcribe_audio_task ──────────────────────────────────────────────────────


class TestTranscribeAudioTask:
    @patch("app.workers.video_tasks._s3_client")
    @patch("app.workers.video_tasks.asyncio.run")
    @patch("app.workers.video_tasks.os.path.exists", return_value=True)
    @patch("app.workers.video_tasks.os.unlink")
    @patch("app.workers.video_tasks.tempfile.mkstemp", return_value=(0, "/tmp/fake.mp4"))
    @patch("app.workers.video_tasks.os.close")
    def test_happy_path(
        self,
        mock_close,
        mock_mkstemp,
        mock_unlink,
        mock_exists,
        mock_run,
        mock_s3_client,
    ):
        transcript_result = MagicMock()
        transcript_result.text = "Hello world."
        transcript_result.segments = []
        transcript_result.language = "en"
        transcript_result.error = None
        mock_run.return_value = transcript_result

        mock_s3 = MagicMock()
        mock_s3_client.return_value = mock_s3

        from app.workers.video_tasks import transcribe_audio_task

        result = transcribe_audio_task(_VIDEO_ID, _S3_KEY)

        assert result["text"] == "Hello world."
        assert result["language"] == "en"
        assert result["error"] is None

    @patch("app.workers.video_tasks._s3_client")
    @patch("app.workers.video_tasks.tempfile.mkstemp", return_value=(0, "/tmp/fake.mp4"))
    @patch("app.workers.video_tasks.os.close")
    @patch("app.workers.video_tasks.os.path.exists", return_value=False)
    def test_s3_failure_triggers_retry(self, mock_exists, mock_close, mock_mkstemp, mock_s3_client):
        mock_s3 = MagicMock()
        mock_s3.download_file.side_effect = Exception("S3 connection refused")
        mock_s3_client.return_value = mock_s3

        from app.workers.video_tasks import transcribe_audio_task

        with pytest.raises(Exception):  # noqa: B017 — retry wraps varied error types
            transcribe_audio_task.apply(args=[_VIDEO_ID, _S3_KEY]).get(propagate=True)


# ── generate_thumbnail_task ────────────────────────────────────────────────────


class TestGenerateThumbnailTask:
    @patch("app.workers.video_tasks.sync_session")
    @patch("app.workers.video_tasks._s3_client")
    @patch("app.workers.video_tasks.subprocess.run")
    @patch(
        "app.workers.video_tasks.tempfile.mkstemp",
        side_effect=[(0, "/tmp/v.mp4"), (0, "/tmp/t.jpg")],
    )
    @patch("app.workers.video_tasks.os.close")
    @patch("app.workers.video_tasks.os.path.exists", return_value=True)
    @patch("app.workers.video_tasks.os.unlink")
    def test_happy_path_returns_thumb_key(
        self,
        mock_unlink,
        mock_exists,
        mock_close,
        mock_mkstemp,
        mock_subprocess,
        mock_s3_client,
        mock_sync_session,
    ):
        mock_subprocess.return_value = MagicMock(returncode=0)
        mock_s3 = MagicMock()
        mock_s3_client.return_value = mock_s3

        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.get.return_value = MagicMock()
        mock_sync_session.return_value = mock_db

        from app.workers.video_tasks import generate_thumbnail_task

        result = generate_thumbnail_task(_VIDEO_ID, _S3_KEY)

        assert result == f"thumbnails/{_VIDEO_ID}.jpg"

    @patch("app.workers.video_tasks._s3_client")
    @patch("app.workers.video_tasks.subprocess.run")
    @patch(
        "app.workers.video_tasks.tempfile.mkstemp",
        side_effect=[(0, "/tmp/v.mp4"), (0, "/tmp/t.jpg")],
    )
    @patch("app.workers.video_tasks.os.close")
    @patch("app.workers.video_tasks.os.path.exists", return_value=True)
    @patch("app.workers.video_tasks.os.unlink")
    def test_ffmpeg_failure_returns_none(
        self,
        mock_unlink,
        mock_exists,
        mock_close,
        mock_mkstemp,
        mock_subprocess,
        mock_s3_client,
    ):
        mock_subprocess.return_value = MagicMock(returncode=1, stderr=b"error")
        mock_s3 = MagicMock()
        mock_s3_client.return_value = mock_s3

        from app.workers.video_tasks import generate_thumbnail_task

        result = generate_thumbnail_task(_VIDEO_ID, _S3_KEY)

        assert result is None


# ── run_analysis_pipeline_task ─────────────────────────────────────────────────


class TestRunAnalysisPipelineTask:
    @patch("app.workers.video_tasks.sync_session")
    @patch("app.workers.video_tasks.asyncio.run")
    def test_happy_path_writes_moderation_result(self, mock_run, mock_sync_session):
        mock_run.return_value = _fake_report()

        mock_video = MagicMock()
        mock_video.tenant_id = None
        mock_video.owner_id = None
        mock_video.title = "Test Video"

        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.get.return_value = mock_video
        mock_sync_session.return_value = mock_db

        from app.workers.video_tasks import run_analysis_pipeline_task

        result = run_analysis_pipeline_task(_VIDEO_ID, _S3_KEY)

        assert result["decision"] == "approved"
        assert result["confidence"] == 0.92
        assert mock_db.add.call_count == 2  # ModerationResult + AnalyticsEvent

    @patch("app.workers.video_tasks.sync_session")
    @patch("app.workers.video_tasks.asyncio.run")
    def test_existing_moderation_result_is_updated(self, mock_run, mock_sync_session):
        mock_run.return_value = _fake_report()

        mock_video = MagicMock()
        mock_video.tenant_id = None
        mock_video.owner_id = None
        mock_video.title = "Test Video"

        existing = MagicMock()
        mock_db = MagicMock()
        mock_db.__enter__ = lambda s: mock_db
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.query.return_value.filter.return_value.first.return_value = existing
        mock_db.get.return_value = mock_video
        mock_sync_session.return_value = mock_db

        from app.workers.video_tasks import run_analysis_pipeline_task

        run_analysis_pipeline_task(_VIDEO_ID, _S3_KEY)

        assert mock_db.add.call_count == 1  # Only AnalyticsEvent (existing result updated in-place)
        assert existing.status is not None

    @patch("app.workers.video_tasks._set_video_status")
    @patch("app.workers.video_tasks.asyncio.run")
    def test_pipeline_failure_marks_video_failed(self, mock_run, mock_set_status):
        mock_run.side_effect = RuntimeError("LangGraph error")

        from app.workers.video_tasks import run_analysis_pipeline_task

        with pytest.raises(Exception):  # noqa: B017 — retry wraps varied error types
            run_analysis_pipeline_task.apply(args=[_VIDEO_ID, _S3_KEY]).get(propagate=True)

        mock_set_status.assert_called()


# ── process_video ──────────────────────────────────────────────────────────────


class TestProcessVideo:
    @patch("app.workers.video_tasks.run_analysis_pipeline_task")
    @patch("app.workers.video_tasks.generate_thumbnail_task")
    @patch("app.workers.video_tasks.transcribe_audio_task")
    @patch("app.workers.video_tasks.extract_frames_task")
    @patch("app.workers.video_tasks._set_video_status")
    def test_happy_path_calls_all_steps(
        self,
        mock_set_status,
        mock_frames,
        mock_transcribe,
        mock_thumbnail,
        mock_pipeline,
    ):
        mock_frames.return_value = {
            "frames": ["f1"],
            "timestamps": [0.0],
            "fps": 25.0,
            "duration": 10.0,
        }
        mock_transcribe.return_value = {
            "text": "hello",
            "segments": [],
            "language": "en",
            "error": None,
        }
        mock_thumbnail.return_value = f"thumbnails/{_VIDEO_ID}.jpg"
        mock_pipeline.return_value = {"decision": "approved", "confidence": 0.9}

        from app.workers.video_tasks import process_video

        result = process_video(_VIDEO_ID, _S3_KEY)

        assert result["decision"] == "approved"
        mock_set_status.assert_called()
        mock_frames.assert_called_once()
        mock_transcribe.assert_called_once()
        mock_pipeline.assert_called_once()

    @patch("app.workers.video_tasks.run_analysis_pipeline_task")
    @patch("app.workers.video_tasks.generate_thumbnail_task")
    @patch("app.workers.video_tasks.transcribe_audio_task")
    @patch("app.workers.video_tasks.extract_frames_task")
    @patch("app.workers.video_tasks._set_video_status")
    def test_thumbnail_failure_does_not_abort_pipeline(
        self,
        mock_set_status,
        mock_frames,
        mock_transcribe,
        mock_thumbnail,
        mock_pipeline,
    ):
        mock_frames.return_value = {
            "frames": [],
            "timestamps": [],
            "fps": 25.0,
            "duration": 5.0,
        }
        mock_transcribe.return_value = {
            "text": "",
            "segments": [],
            "language": "en",
            "error": None,
        }
        mock_thumbnail.side_effect = Exception("S3 upload failed")
        mock_pipeline.return_value = {"decision": "approved", "confidence": 0.8}

        from app.workers.video_tasks import process_video

        result = process_video(_VIDEO_ID, _S3_KEY)

        # Pipeline still completes despite thumbnail failure
        assert result["decision"] == "approved"
        mock_pipeline.assert_called_once()
