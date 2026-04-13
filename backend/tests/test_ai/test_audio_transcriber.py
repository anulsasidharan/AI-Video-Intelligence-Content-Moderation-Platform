"""Tests for T-02 AudioTranscriber — FFmpeg subprocess and OpenAI Whisper mocked."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.tools.audio_transcriber import (
    AudioTranscriptionError,
    TranscriptResult,
    _extract_audio_ffmpeg,
    transcribe_audio,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _mock_whisper_response(
    text: str = "Hello world.",
    language: str = "en",
    segments: list[dict] | None = None,
) -> MagicMock:
    resp = MagicMock()
    resp.text = text
    resp.language = language
    resp.segments = segments or [{"start": 0.0, "end": 1.5, "text": text}]
    return resp


def _mock_openai_client(response: MagicMock | None = None, side_effect=None) -> MagicMock:
    client = MagicMock()
    client.audio.transcriptions.create = AsyncMock(return_value=response, side_effect=side_effect)
    return client


# ── _extract_audio_ffmpeg ─────────────────────────────────────────────────────


@patch("app.ai.tools.audio_transcriber.subprocess.run")
def test_extract_audio_ffmpeg_success(mock_run):
    mock_run.return_value = MagicMock(returncode=0)
    _extract_audio_ffmpeg("/in.mp4", "/out.wav")  # should not raise
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "ffmpeg" in cmd
    assert "/in.mp4" in cmd
    assert "/out.wav" in cmd


@patch("app.ai.tools.audio_transcriber.subprocess.run")
def test_extract_audio_ffmpeg_nonzero_exit_raises(mock_run):
    mock_run.return_value = MagicMock(returncode=1, stderr=b"codec error")
    with pytest.raises(AudioTranscriptionError, match="FFmpeg audio extraction failed"):
        _extract_audio_ffmpeg("/bad.mp4", "/out.wav")


# ── transcribe_audio ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("app.ai.tools.audio_transcriber._extract_audio_ffmpeg")
@patch("app.ai.tools.audio_transcriber.os.path.exists", return_value=True)
@patch("app.ai.tools.audio_transcriber.os.unlink")
@patch("builtins.open", new_callable=MagicMock)
async def test_transcribe_audio_happy_path(mock_open, mock_unlink, mock_exists, mock_ffmpeg):
    mock_ffmpeg.return_value = None  # success
    mock_open.return_value.__enter__ = lambda s: s
    mock_open.return_value.__exit__ = MagicMock(return_value=False)
    mock_open.return_value.read = MagicMock(return_value=b"")

    client = _mock_openai_client(
        response=_mock_whisper_response(
            text="Today we make pasta.",
            language="en",
            segments=[{"start": 0.0, "end": 3.0, "text": "Today we make pasta."}],
        )
    )

    result = await transcribe_audio("/tmp/video.mp4", _client=client)

    assert isinstance(result, TranscriptResult)
    assert result.text == "Today we make pasta."
    assert result.language == "en"
    assert len(result.segments) == 1
    assert result.segments[0].start == 0.0
    assert result.error is None


@pytest.mark.asyncio
@patch("app.ai.tools.audio_transcriber._extract_audio_ffmpeg")
@patch("app.ai.tools.audio_transcriber.os.path.exists", return_value=True)
@patch("app.ai.tools.audio_transcriber.os.unlink")
async def test_transcribe_audio_ffmpeg_failure_returns_empty(mock_unlink, mock_exists, mock_ffmpeg):
    mock_ffmpeg.side_effect = AudioTranscriptionError("no audio stream")

    result = await transcribe_audio("/no_audio.mp4", _client=MagicMock())

    assert result.text == ""
    assert result.segments == []
    assert "no audio stream" in (result.error or "")


@pytest.mark.asyncio
@patch("app.ai.tools.audio_transcriber._extract_audio_ffmpeg")
@patch("app.ai.tools.audio_transcriber.os.path.exists", return_value=True)
@patch("app.ai.tools.audio_transcriber.os.unlink")
@patch("builtins.open", new_callable=MagicMock)
async def test_transcribe_audio_whisper_failure_returns_empty(
    mock_open, mock_unlink, mock_exists, mock_ffmpeg
):
    mock_ffmpeg.return_value = None
    mock_open.return_value.__enter__ = lambda s: s
    mock_open.return_value.__exit__ = MagicMock(return_value=False)

    client = _mock_openai_client(side_effect=Exception("Whisper 503"))

    result = await transcribe_audio("/tmp/video.mp4", _client=client)

    assert result.text == ""
    assert "Whisper 503" in (result.error or "")


@pytest.mark.asyncio
@patch("app.ai.tools.audio_transcriber._extract_audio_ffmpeg")
@patch("app.ai.tools.audio_transcriber.os.path.exists", return_value=True)
@patch("app.ai.tools.audio_transcriber.os.unlink")
@patch("builtins.open", new_callable=MagicMock)
async def test_transcribe_audio_language_hint_passed_to_whisper(
    mock_open, mock_unlink, mock_exists, mock_ffmpeg
):
    mock_ffmpeg.return_value = None
    mock_open.return_value.__enter__ = lambda s: s
    mock_open.return_value.__exit__ = MagicMock(return_value=False)

    resp = _mock_whisper_response(text="Bonjour.", language="fr")
    client = _mock_openai_client(response=resp)

    result = await transcribe_audio("/tmp/video.mp4", language="fr", _client=client)

    call_kwargs = client.audio.transcriptions.create.call_args.kwargs
    assert call_kwargs.get("language") == "fr"
    assert result.language == "fr"


@pytest.mark.asyncio
@patch("app.ai.tools.audio_transcriber._extract_audio_ffmpeg")
@patch("app.ai.tools.audio_transcriber.os.path.exists", return_value=True)
@patch("app.ai.tools.audio_transcriber.os.unlink")
@patch("builtins.open", new_callable=MagicMock)
async def test_transcribe_audio_no_segments_returns_empty_list(
    mock_open, mock_unlink, mock_exists, mock_ffmpeg
):
    mock_ffmpeg.return_value = None
    mock_open.return_value.__enter__ = lambda s: s
    mock_open.return_value.__exit__ = MagicMock(return_value=False)

    resp = _mock_whisper_response(text="OK.", segments=None)
    resp.segments = None
    client = _mock_openai_client(response=resp)

    result = await transcribe_audio("/tmp/video.mp4", _client=client)
    assert result.segments == []
    assert result.error is None
