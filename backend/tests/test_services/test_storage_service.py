"""Tests for S-05 StorageService — google-cloud-storage client mocked."""

from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import pytest
from google.cloud.exceptions import NotFound


class TestStorageService:
    def _make_service(self, mock_bucket=None):
        from app.services.storage_service import StorageService

        mock_client = MagicMock()
        if mock_bucket is not None:
            mock_client.bucket.return_value = mock_bucket

        with patch("app.services.storage_service._build_client", return_value=mock_client):
            return StorageService(bucket_name="test-bucket", client=mock_client)

    # ── presigned_put_url ──────────────────────────────────────────────────────

    def test_presigned_put_url_returns_url(self):
        mock_blob = MagicMock()
        mock_blob.generate_signed_url.return_value = "https://storage.googleapis.com/put-url"
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob

        service = self._make_service(mock_bucket)
        url = service.presigned_put_url("videos/test.mp4", content_type="video/mp4", expires=300)

        assert url == "https://storage.googleapis.com/put-url"
        mock_blob.generate_signed_url.assert_called_once()
        call_kwargs = mock_blob.generate_signed_url.call_args.kwargs
        assert call_kwargs["method"] == "PUT"
        assert call_kwargs["content_type"] == "video/mp4"

    # ── presigned_get_url ──────────────────────────────────────────────────────

    def test_presigned_get_url_returns_url(self):
        mock_blob = MagicMock()
        mock_blob.generate_signed_url.return_value = "https://storage.googleapis.com/get-url"
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob

        service = self._make_service(mock_bucket)
        url = service.presigned_get_url("videos/test.mp4", expires=600)

        assert url == "https://storage.googleapis.com/get-url"
        call_kwargs = mock_blob.generate_signed_url.call_args.kwargs
        assert call_kwargs["method"] == "GET"

    # ── delete_object ──────────────────────────────────────────────────────────

    def test_delete_object_calls_blob_delete(self):
        mock_blob = MagicMock()
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob

        service = self._make_service(mock_bucket)
        service.delete_object("videos/old.mp4")
        mock_blob.delete.assert_called_once()

    # ── object_exists ──────────────────────────────────────────────────────────

    def test_object_exists_returns_true_when_found(self):
        mock_blob = MagicMock()
        mock_blob.exists.return_value = True
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob

        service = self._make_service(mock_bucket)
        assert service.object_exists("videos/exists.mp4") is True

    def test_object_exists_returns_false_when_missing(self):
        mock_blob = MagicMock()
        mock_blob.exists.return_value = False
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob

        service = self._make_service(mock_bucket)
        assert service.object_exists("videos/missing.mp4") is False

    # ── upload_fileobj ─────────────────────────────────────────────────────────

    def test_upload_fileobj_calls_blob_upload(self):
        mock_blob = MagicMock()
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob

        service = self._make_service(mock_bucket)
        fileobj = io.BytesIO(b"video data")
        service.upload_fileobj(fileobj, "videos/new.mp4", content_type="video/mp4")
        mock_blob.upload_from_file.assert_called_once_with(fileobj, content_type="video/mp4")

    # ── delete_objects_batch ───────────────────────────────────────────────────

    def test_delete_objects_batch_counts_correctly(self):
        mock_bucket = MagicMock()
        blob_ok = MagicMock()
        blob_missing = MagicMock()
        blob_missing.delete.side_effect = NotFound("gone")
        mock_bucket.blob.side_effect = lambda key: blob_missing if "missing" in key else blob_ok

        service = self._make_service(mock_bucket)
        deleted, errors = service.delete_objects_batch(["videos/a.mp4", "videos/missing.mp4"])
        assert deleted == 2  # NotFound still counts as deleted
        assert errors == 0

    # ── get_storage_service dependency ────────────────────────────────────────

    def test_get_storage_service_returns_instance(self):
        from app.services.storage_service import StorageService, get_storage_service

        with patch("app.services.storage_service._build_client", return_value=MagicMock()):
            service = get_storage_service()
        assert isinstance(service, StorageService)
