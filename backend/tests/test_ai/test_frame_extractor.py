"""Tests for T-01 FrameExtractor — OpenCV and boto3 mocked."""

from __future__ import annotations

import base64
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.ai.tools.frame_extractor import (
    FrameExtractionError,
    FrameExtractionResult,
    _download_from_s3,
    _extract_local,
    extract_frames,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_mock_cap(
    *,
    fps: float = 25.0,
    total_frames: int = 100,
    frame_data: np.ndarray | None = None,
    read_returns: list[tuple[bool, np.ndarray]] | None = None,
) -> MagicMock:
    """Build a cv2.VideoCapture mock that returns configurable frame data."""
    if frame_data is None:
        frame_data = np.zeros((64, 64, 3), dtype=np.uint8)

    cap = MagicMock()
    cap.isOpened.return_value = True
    cap.get.side_effect = lambda prop: {
        0: fps,  # CAP_PROP_FPS
        7: total_frames,  # CAP_PROP_FRAME_COUNT
    }.get(prop, 0.0)

    if read_returns is not None:
        cap.read.side_effect = read_returns
    else:
        cap.read.return_value = (True, frame_data)

    return cap


def _b64_jpeg() -> str:
    """Return a minimal valid base64 JPEG string for assertions."""
    # Any non-empty b64 string — actual JPEG encoding comes from cv2 in real code
    return base64.b64encode(b"\xff\xd8\xff").decode()


# ── _extract_local ─────────────────────────────────────────────────────────────


@patch("app.ai.tools.frame_extractor.cv2.VideoCapture")
@patch("app.ai.tools.frame_extractor.cv2.imencode")
def test_extract_local_happy_path(mock_imencode, mock_cap_cls):
    fake_buf = MagicMock()
    fake_buf.tobytes.return_value = b"\xff\xd8\xff"
    mock_imencode.return_value = (True, fake_buf)
    mock_cap_cls.return_value = _make_mock_cap(fps=25.0, total_frames=75)

    result = _extract_local("fake.mp4", interval_seconds=1.0, max_frames=3)

    assert isinstance(result, FrameExtractionResult)
    assert len(result.frames) == 3
    assert len(result.timestamps) == 3
    assert result.fps == 25.0
    assert result.frame_count_extracted == 3


@patch("app.ai.tools.frame_extractor.cv2.VideoCapture")
def test_extract_local_cannot_open_raises(mock_cap_cls):
    cap = MagicMock()
    cap.isOpened.return_value = False
    mock_cap_cls.return_value = cap

    with pytest.raises(FrameExtractionError, match="Cannot open video"):
        _extract_local("missing.mp4", interval_seconds=1.0, max_frames=5)


@patch("app.ai.tools.frame_extractor.cv2.VideoCapture")
@patch("app.ai.tools.frame_extractor.cv2.imencode")
def test_extract_local_read_returns_false_stops_early(mock_imencode, mock_cap_cls):
    """If cap.read() returns False before max_frames, extraction stops gracefully."""
    fake_buf = MagicMock()
    fake_buf.tobytes.return_value = b"\xff\xd8\xff"
    mock_imencode.return_value = (True, fake_buf)

    cap = _make_mock_cap(fps=25.0, total_frames=50)
    cap.read.side_effect = [(True, MagicMock()), (False, None)]
    mock_cap_cls.return_value = cap

    result = _extract_local("fake.mp4", interval_seconds=1.0, max_frames=10)
    assert len(result.frames) == 1


@patch("app.ai.tools.frame_extractor.cv2.VideoCapture")
@patch("app.ai.tools.frame_extractor.cv2.imencode")
def test_extract_local_encode_failure_skips_frame(mock_imencode, mock_cap_cls):
    """Frames that fail JPEG encoding are skipped, not raised.
    total_frames=3 ensures the while condition (frame_idx < total_frames) terminates.
    """
    mock_imencode.return_value = (False, None)  # encoding always fails
    # Use total_frames=3 so the loop exits after exhausting all frame positions
    mock_cap_cls.return_value = _make_mock_cap(fps=1.0, total_frames=3)

    result = _extract_local("fake.mp4", interval_seconds=1.0, max_frames=10)
    # All frames skipped — should return empty but not raise
    assert result.frames == []


@patch("app.ai.tools.frame_extractor.cv2.VideoCapture")
@patch("app.ai.tools.frame_extractor.cv2.imencode")
def test_extract_local_zero_fps_fallback(mock_imencode, mock_cap_cls):
    """If FPS is 0, extraction should fall back to 25 fps safely."""
    fake_buf = MagicMock()
    fake_buf.tobytes.return_value = b"\xff\xd8\xff"
    mock_imencode.return_value = (True, fake_buf)

    cap = _make_mock_cap(fps=0.0, total_frames=50)
    mock_cap_cls.return_value = cap

    result = _extract_local("fake.mp4", interval_seconds=1.0, max_frames=2)
    assert result.fps == 25.0


# ── extract_frames (S3 path) ──────────────────────────────────────────────────


@patch("app.ai.tools.frame_extractor._download_from_s3")
@patch("app.ai.tools.frame_extractor._extract_local")
def test_extract_frames_s3_url_downloads_then_extracts(mock_extract, mock_download):
    mock_download.return_value = "/tmp/downloaded.mp4"
    mock_extract.return_value = FrameExtractionResult(
        frames=["abc"],
        timestamps=[0.0],
        fps=25.0,
        duration=10.0,
        frame_count_extracted=1,
    )

    result = extract_frames("s3://my-bucket/video.mp4", interval_seconds=2.0, max_frames=5)

    mock_download.assert_called_once_with("s3://my-bucket/video.mp4")
    mock_extract.assert_called_once()
    assert len(result.frames) == 1


@patch("app.ai.tools.frame_extractor.cv2.VideoCapture")
@patch("app.ai.tools.frame_extractor.cv2.imencode")
def test_extract_frames_local_path_no_s3(mock_imencode, mock_cap_cls):
    fake_buf = MagicMock()
    fake_buf.tobytes.return_value = b"\xff\xd8\xff"
    mock_imencode.return_value = (True, fake_buf)
    mock_cap_cls.return_value = _make_mock_cap()

    result = extract_frames("/local/video.mp4", interval_seconds=1.0, max_frames=2)
    assert result.frame_count_extracted == 2


# ── _download_from_s3 ─────────────────────────────────────────────────────────


def test_download_from_s3_invalid_scheme_raises():
    with pytest.raises(FrameExtractionError, match="Unsupported URL scheme"):
        _download_from_s3("https://example.com/video.mp4")


def test_download_from_s3_missing_key_raises():
    with pytest.raises(FrameExtractionError, match="Invalid S3 URL"):
        _download_from_s3("s3://bucket-only")
