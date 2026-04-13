"""
S-05 StorageService

Google Cloud Storage abstraction: signed URLs, object upload/download,
existence check, and deletion. No database dependency — constructed from
config values.

Public API:
    service.presigned_put_url(object_key, content_type, expires) -> str
    service.presigned_get_url(object_key, expires) -> str
    service.delete_object(object_key) -> None
    service.object_exists(object_key) -> bool
    service.upload_fileobj(fileobj, object_key, content_type) -> None
    service.download_object(object_key) -> bytes
    service.list_objects_with_prefix(prefix) -> list[str]

FastAPI dependency:
    get_storage_service() -> StorageService

Authentication:
    - Local dev: set GCS_SERVICE_ACCOUNT_KEY_PATH to a service-account JSON key
      file, or export GOOGLE_APPLICATION_CREDENTIALS to the same path.
    - GKE (Workload Identity): leave both blank — ADC handles everything,
      including blob signing via the attached service account.
"""

from __future__ import annotations

import datetime
from typing import IO, Any

import structlog
from google.cloud import storage
from google.cloud.exceptions import NotFound

from app.config import settings

logger = structlog.get_logger(__name__)

_DEFAULT_PRESIGNED_EXPIRES = settings.GCS_PRESIGNED_URL_EXPIRE  # seconds


def _build_client() -> storage.Client:
    """Return a GCS client.

    Uses Application Default Credentials (ADC), which resolves to:
      - A service-account JSON key when GOOGLE_APPLICATION_CREDENTIALS is set.
      - GKE Workload Identity when running inside GKE.
      - User credentials from `gcloud auth application-default login` locally.
    """
    kwargs: dict[str, Any] = {}
    if settings.GCP_PROJECT_ID:
        kwargs["project"] = settings.GCP_PROJECT_ID
    if settings.GCS_SERVICE_ACCOUNT_KEY_PATH:
        return storage.Client.from_service_account_json(
            settings.GCS_SERVICE_ACCOUNT_KEY_PATH, **kwargs
        )
    return storage.Client(**kwargs)


class StorageService:
    """Thin wrapper around the google-cloud-storage client."""

    def __init__(
        self,
        bucket_name: str,
        client: storage.Client | None = None,
    ) -> None:
        self._bucket_name = bucket_name
        self._client = client or _build_client()
        self._bucket = self._client.bucket(bucket_name)

    # ── Presigned / Signed URLs ────────────────────────────────────────────────

    def presigned_put_url(
        self,
        object_key: str,
        content_type: str = "application/octet-stream",
        expires: int = _DEFAULT_PRESIGNED_EXPIRES,
    ) -> str:
        """
        Generate a V4 signed PUT URL so clients can upload directly to GCS.

        Args:
            object_key:   Destination object name inside the bucket.
            content_type: MIME type declared by the client.
            expires:      URL validity in seconds.

        Returns:
            Signed URL string.
        """
        blob = self._bucket.blob(object_key)
        url: str = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(seconds=expires),
            method="PUT",
            content_type=content_type,
        )
        logger.info("presigned_put_url_generated", object_key=object_key, expires=expires)
        return url

    def presigned_get_url(
        self,
        object_key: str,
        expires: int = _DEFAULT_PRESIGNED_EXPIRES,
    ) -> str:
        """
        Generate a V4 signed GET URL for temporary read access.

        Args:
            object_key: Object name inside the bucket.
            expires:    URL validity in seconds.

        Returns:
            Signed URL string.
        """
        blob = self._bucket.blob(object_key)
        url: str = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(seconds=expires),
            method="GET",
        )
        logger.info("presigned_get_url_generated", object_key=object_key, expires=expires)
        return url

    # ── Object operations ──────────────────────────────────────────────────────

    def delete_object(self, object_key: str) -> None:
        """
        Permanently delete an object from GCS.

        Args:
            object_key: Object name to delete.
        """
        blob = self._bucket.blob(object_key)
        blob.delete()
        logger.info("gcs_object_deleted", object_key=object_key)

    def object_exists(self, object_key: str) -> bool:
        """
        Check whether an object exists.

        Args:
            object_key: Object name to check.

        Returns:
            True if the object exists, False otherwise.
        """
        blob = self._bucket.blob(object_key)
        return blob.exists()

    def upload_fileobj(
        self,
        fileobj: IO[Any],
        s3_key: str,  # kept as s3_key for backwards-compat with callers/Celery args
        content_type: str = "application/octet-stream",
    ) -> None:
        """
        Upload a file-like object to GCS.

        Args:
            fileobj:      File-like object opened in binary mode.
            s3_key:       Destination object name (field name kept for compatibility).
            content_type: MIME type of the object.
        """
        blob = self._bucket.blob(s3_key)
        blob.upload_from_file(fileobj, content_type=content_type)
        logger.info("gcs_object_uploaded", object_key=s3_key)

    def download_object(self, object_key: str) -> bytes:
        """
        Download a GCS object and return its raw bytes.

        Args:
            object_key: Object name to download.

        Returns:
            Object content as bytes.
        """
        blob = self._bucket.blob(object_key)
        data: bytes = blob.download_as_bytes()
        logger.info("gcs_object_downloaded", object_key=object_key, size=len(data))
        return data

    def download_to_file(self, object_key: str, destination_path: str) -> None:
        """
        Download a GCS object directly to a local file path.

        Args:
            object_key:        Object name to download.
            destination_path:  Local file path to write to.
        """
        blob = self._bucket.blob(object_key)
        blob.download_to_filename(destination_path)
        logger.info("gcs_object_downloaded_to_file", object_key=object_key, path=destination_path)

    def upload_file(self, source_path: str, object_key: str, content_type: str = "application/octet-stream") -> None:
        """
        Upload a local file to GCS by path.

        Args:
            source_path:  Local file path to read from.
            object_key:   Destination object name in the bucket.
            content_type: MIME type of the object.
        """
        blob = self._bucket.blob(object_key)
        blob.upload_from_filename(source_path, content_type=content_type)
        logger.info("gcs_file_uploaded", object_key=object_key, source=source_path)

    def list_objects_with_prefix(self, prefix: str) -> list[str]:
        """
        List all object names under a given prefix.

        Args:
            prefix: Object name prefix to list.

        Returns:
            List of object names.
        """
        blobs = self._client.list_blobs(self._bucket_name, prefix=prefix)
        return [blob.name for blob in blobs]

    def list_blobs_with_metadata(self, prefix: str) -> list[storage.Blob]:
        """
        List blobs with full metadata (including time_created) under a prefix.

        Args:
            prefix: Object name prefix to list.

        Returns:
            List of Blob objects.
        """
        return list(self._client.list_blobs(self._bucket_name, prefix=prefix))

    def delete_objects_batch(self, object_keys: list[str]) -> tuple[int, int]:
        """
        Delete multiple objects. Returns (deleted_count, error_count).

        GCS has no native batch-delete endpoint like S3; objects are deleted
        individually. Use in background tasks where latency is acceptable.

        Args:
            object_keys: List of object names to delete.

        Returns:
            Tuple of (deleted, errors).
        """
        deleted = errors = 0
        for key in object_keys:
            try:
                self._bucket.blob(key).delete()
                deleted += 1
            except NotFound:
                deleted += 1  # already gone — treat as success
            except Exception as exc:
                logger.warning("gcs_batch_delete_error", object_key=key, error=str(exc))
                errors += 1
        return deleted, errors


# ── FastAPI dependency ─────────────────────────────────────────────────────────


def get_storage_service() -> StorageService:
    """FastAPI dependency that returns a configured StorageService instance."""
    return StorageService(bucket_name=settings.GCS_BUCKET_NAME)
