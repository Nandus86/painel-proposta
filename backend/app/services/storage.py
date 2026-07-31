import os
import uuid
import json
import mimetypes
from io import BytesIO
from typing import Optional, Tuple
from fastapi import UploadFile
from app.config import settings


class StorageService:
    def __init__(self):
        self._minio_client = None

    def _is_minio_configured(self) -> bool:
        if settings.STORAGE_PROVIDER.lower() == "minio":
            return True
        return bool(settings.MINIO_ENDPOINT and settings.MINIO_ACCESS_KEY and settings.MINIO_SECRET_KEY)

    def _get_minio_client(self):
        if self._minio_client is not None:
            return self._minio_client

        try:
            from minio import Minio
        except ImportError:
            raise RuntimeError("A biblioteca 'minio' não está instalada. Execute: pip install minio")

        # Strip protocol if user included http:// or https:// in MINIO_ENDPOINT
        endpoint = settings.MINIO_ENDPOINT or ""
        endpoint = endpoint.replace("http://", "").replace("https://", "").rstrip("/")

        self._minio_client = Minio(
            endpoint=endpoint,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        return self._minio_client

    def _ensure_bucket_exists(self, client, bucket_name: str):
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            # Set public read policy so uploaded images can be fetched directly by browsers
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": ["*"]},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{bucket_name}/*"],
                    }
                ],
            }
            try:
                client.set_bucket_policy(bucket_name, json.dumps(policy))
            except Exception as e:
                print(f"[StorageService] Warning setting bucket policy: {e}")

    async def upload_file(self, file: UploadFile, folder: str = "logos") -> str:
        """
        Uploads a file to MinIO (if configured) or local disk, and returns the file URL/path.
        """
        content = await file.read()
        filename = file.filename or "file"
        ext = os.path.splitext(filename)[1].lower()
        if not ext and file.content_type:
            ct_map = {
                "image/png": ".png",
                "image/jpeg": ".jpg",
                "image/jpg": ".jpg",
                "image/webp": ".webp",
                "image/gif": ".gif",
                "image/svg+xml": ".svg",
            }
            ext = ct_map.get(file.content_type.lower(), ".bin")

        unique_name = f"{uuid.uuid4().hex}{ext}"
        object_key = f"{folder}/{unique_name}"

        if self._is_minio_configured():
            try:
                client = self._get_minio_client()
                bucket_name = settings.MINIO_BUCKET_NAME
                self._ensure_bucket_exists(client, bucket_name)

                content_type = file.content_type or "application/octet-stream"
                client.put_object(
                    bucket_name=bucket_name,
                    object_name=object_key,
                    data=BytesIO(content),
                    length=len(content),
                    content_type=content_type,
                )

                if settings.MINIO_PUBLIC_URL:
                    base_url = settings.MINIO_PUBLIC_URL.rstrip("/")
                    return f"{base_url}/{bucket_name}/{object_key}"

                # If no explicit public MinIO URL is set, return relative path served by FastAPI
                return f"/uploads/{folder}/{unique_name}"
            except Exception as e:
                print(f"[StorageService] MinIO upload error: {e}. Falling back to local storage.")

        # Local storage fallback
        target_dir = os.path.join("uploads", folder)
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, unique_name)

        with open(file_path, "wb") as f:
            f.write(content)

        # Normalize path separators for URL
        url_path = f"/uploads/{folder}/{unique_name}".replace("\\", "/")
        return url_path

    async def get_file_content(self, object_key: str) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Retrieves file bytes and content-type from local storage or MinIO.
        Returns (content, content_type) or (None, None) if not found.
        """
        object_key = object_key.lstrip("/")

        # 1. Try local file first
        local_path = os.path.join("uploads", object_key)
        if os.path.isfile(local_path):
            content_type, _ = mimetypes.guess_type(local_path)
            with open(local_path, "rb") as f:
                return f.read(), content_type or "application/octet-stream"

        # 2. Try MinIO if configured
        if self._is_minio_configured():
            try:
                client = self._get_minio_client()
                bucket_name = settings.MINIO_BUCKET_NAME
                response = client.get_object(bucket_name, object_key)
                data = response.read()
                content_type = response.headers.get("Content-Type") or "application/octet-stream"
                response.close()
                response.release_conn()
                return data, content_type
            except Exception as e:
                print(f"[StorageService] Error reading '{object_key}' from MinIO: {e}")

        return None, None


storage_service = StorageService()
