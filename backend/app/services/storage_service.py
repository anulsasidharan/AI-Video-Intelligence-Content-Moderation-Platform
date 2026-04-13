"""
S-05 StorageService

AWS S3 abstraction: presigned URLs, object upload/download, existence check,
and deletion. No database dependency — constructed from config values.

Public API:
    service.presigned_put_url(s3_key, content_type, expires) -> str
    service.presigned_get_url(s3_key, expires) -> str
    service.delete_object(s3_key) -> None
    service.object_exists(s3_key) -> bool
    service.upload_fileobj(fileobj, s3_key, content_type) -> None

FastAPI dependency:
    get_storage_service() -> StorageService
"""

from __future__ import annotations

from typing import IO, Any

import boto3
import structlog
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import settings

logger = structlog.get_logger(__name__)

_DEFAULT_PRESIGNED_EXPIRES = settings.S3_PRESIGNED_URL_EXPIRE  # seconds


class StorageService:
    """Thin wrapper around boto3 S3 client."""

    def __init__(
        self,
        bucket: str,
        region: str,
        access_key: str | None = None,
        secret_key: str | None = None,
    ) -> None:
        self._bucket = bucket
        self._region = region
        self._client = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=access_key or None,
            aws_secret_access_key=secret_key or None,
            config=Config(signature_version="s3v4"),  # SigV2 is deprecated; SigV4 required for CORS
        )

    # ── Presigned URLs ─────────────────────────────────────────────────────────

    def presigned_put_url(
        self,
        s3_key: str,
        content_type: str = "application/octet-stream",
        expires: int = _DEFAULT_PRESIGNED_EXPIRES,
    ) -> str:
        """
        Generate a pre-signed PUT URL so clients can upload directly to S3.

        Args:
            s3_key:       Destination object key.
            content_type: MIME type declared by the client.
            expires:      URL validity in seconds.

        Returns:
            Presigned URL string.
        """
        url: str = self._client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self._bucket,
                "Key": s3_key,
                "ContentType": content_type,
            },
            ExpiresIn=expires,
        )
        logger.info("presigned_put_url_generated", s3_key=s3_key, expires=expires)
        return url

    def presigned_get_url(
        self,
        s3_key: str,
        expires: int = _DEFAULT_PRESIGNED_EXPIRES,
    ) -> str:
        """
        Generate a pre-signed GET URL for temporary read access.

        Args:
            s3_key:  Object key.
            expires: URL validity in seconds.

        Returns:
            Presigned URL string.
        """
        url: str = self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": s3_key},
            ExpiresIn=expires,
        )
        logger.info("presigned_get_url_generated", s3_key=s3_key, expires=expires)
        return url

    # ── Object operations ──────────────────────────────────────────────────────

    def delete_object(self, s3_key: str) -> None:
        """
        Permanently delete an object from S3.

        Args:
            s3_key: Object key to delete.
        """
        self._client.delete_object(Bucket=self._bucket, Key=s3_key)
        logger.info("s3_object_deleted", s3_key=s3_key)

    def object_exists(self, s3_key: str) -> bool:
        """
        Check whether an object exists via a HEAD request.

        Args:
            s3_key: Object key to check.

        Returns:
            True if the object exists, False otherwise.
        """
        try:
            self._client.head_object(Bucket=self._bucket, Key=s3_key)
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return False
            raise

    def upload_fileobj(
        self,
        fileobj: IO[Any],
        s3_key: str,
        content_type: str = "application/octet-stream",
    ) -> None:
        """
        Upload a file-like object to S3.

        Args:
            fileobj:      File-like object opened in binary mode.
            s3_key:       Destination object key.
            content_type: MIME type of the object.
        """
        self._client.upload_fileobj(
            fileobj,
            self._bucket,
            s3_key,
            ExtraArgs={"ContentType": content_type},
        )
        logger.info("s3_object_uploaded", s3_key=s3_key)

    def download_object(self, s3_key: str) -> bytes:
        """
        Download an S3 object and return its raw bytes.

        Args:
            s3_key: Object key to download.

        Returns:
            Object content as bytes.
        """
        response = self._client.get_object(Bucket=self._bucket, Key=s3_key)
        data: bytes = response["Body"].read()
        logger.info("s3_object_downloaded", s3_key=s3_key, size=len(data))
        return data

    def list_objects_with_prefix(self, prefix: str) -> list[str]:
        """
        List all object keys under a given prefix.

        Args:
            prefix: S3 key prefix to list.

        Returns:
            List of object keys.
        """
        keys: list[str] = []
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                keys.append(obj["Key"])
        return keys


# ── FastAPI dependency ─────────────────────────────────────────────────────────


def get_storage_service() -> StorageService:
    """FastAPI dependency that returns a configured StorageService instance."""
    return StorageService(
        bucket=settings.S3_BUCKET_NAME,
        region=settings.AWS_REGION,
        access_key=settings.AWS_ACCESS_KEY_ID or None,
        secret_key=settings.AWS_SECRET_ACCESS_KEY or None,
    )
