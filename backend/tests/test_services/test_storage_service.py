"""Tests for S-05 StorageService — boto3 client mocked."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError


class TestStorageService:
    def _make_service(self, mock_client=None):
        from app.services.storage_service import StorageService

        with patch(
            "app.services.storage_service.boto3.client",
            return_value=mock_client or MagicMock(),
        ):
            return StorageService(
                bucket="test-bucket",
                region="us-east-1",
                access_key="key",
                secret_key="secret",
            )

    # ── presigned_put_url ──────────────────────────────────────────────────────

    def test_presigned_put_url_calls_boto3_and_returns_url(self):
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://s3.example.com/put-url"

        service = self._make_service(mock_client)
        url = service.presigned_put_url("videos/test.mp4", content_type="video/mp4", expires=300)

        assert url == "https://s3.example.com/put-url"
        mock_client.generate_presigned_url.assert_called_once_with(
            "put_object",
            Params={
                "Bucket": "test-bucket",
                "Key": "videos/test.mp4",
                "ContentType": "video/mp4",
            },
            ExpiresIn=300,
        )

    # ── presigned_get_url ──────────────────────────────────────────────────────

    def test_presigned_get_url_calls_boto3(self):
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://s3.example.com/get-url"

        service = self._make_service(mock_client)
        url = service.presigned_get_url("videos/test.mp4", expires=600)

        assert url == "https://s3.example.com/get-url"
        mock_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "videos/test.mp4"},
            ExpiresIn=600,
        )

    # ── delete_object ──────────────────────────────────────────────────────────

    def test_delete_object_calls_boto3(self):
        mock_client = MagicMock()
        service = self._make_service(mock_client)
        service.delete_object("videos/old.mp4")
        mock_client.delete_object.assert_called_once_with(
            Bucket="test-bucket", Key="videos/old.mp4"
        )

    # ── object_exists ──────────────────────────────────────────────────────────

    def test_object_exists_returns_true_when_found(self):
        mock_client = MagicMock()
        mock_client.head_object.return_value = {}
        service = self._make_service(mock_client)
        assert service.object_exists("videos/exists.mp4") is True

    def test_object_exists_returns_false_on_404(self):
        mock_client = MagicMock()
        error = ClientError({"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject")
        mock_client.head_object.side_effect = error
        service = self._make_service(mock_client)
        assert service.object_exists("videos/missing.mp4") is False

    def test_object_exists_re_raises_non_404_errors(self):
        mock_client = MagicMock()
        error = ClientError({"Error": {"Code": "403", "Message": "Forbidden"}}, "HeadObject")
        mock_client.head_object.side_effect = error
        service = self._make_service(mock_client)
        with pytest.raises(ClientError):
            service.object_exists("videos/forbidden.mp4")

    # ── upload_fileobj ─────────────────────────────────────────────────────────

    def test_upload_fileobj_calls_boto3(self):
        import io

        mock_client = MagicMock()
        service = self._make_service(mock_client)
        fileobj = io.BytesIO(b"video data")
        service.upload_fileobj(fileobj, "videos/new.mp4", content_type="video/mp4")
        mock_client.upload_fileobj.assert_called_once_with(
            fileobj,
            "test-bucket",
            "videos/new.mp4",
            ExtraArgs={"ContentType": "video/mp4"},
        )

    # ── get_storage_service dependency ────────────────────────────────────────

    def test_get_storage_service_returns_instance(self):
        from app.services.storage_service import StorageService, get_storage_service

        with patch("app.services.storage_service.boto3.client"):
            service = get_storage_service()
        assert isinstance(service, StorageService)
