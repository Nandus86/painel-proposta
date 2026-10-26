import json
import logging
import mimetypes
import os
import uuid
from io import BytesIO
from typing import Optional, Tuple

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool

from app.config import settings

logger = logging.getLogger(__name__)

# Assinaturas (magic bytes) dos formatos aceitos. SVG fica de fora: pode carregar script.
_IMAGE_SIGNATURES = (
    (b"\x89PNG\r\n\x1a\n", ".png", "image/png"),
    (b"\xff\xd8\xff", ".jpg", "image/jpeg"),
    (b"GIF87a", ".gif", "image/gif"),
    (b"GIF89a", ".gif", "image/gif"),
)


def _detect_image(content: bytes) -> Optional[Tuple[str, str]]:
    for signature, ext, mime in _IMAGE_SIGNATURES:
        if content.startswith(signature):
            return ext, mime
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return ".webp", "image/webp"
    return None


class StorageService:
    def __init__(self):
        self._minio_client = None

    def _is_minio_configured(self) -> bool:
        # Compatível com a configuração antiga: credenciais completas já ativam o MinIO
        return bool(settings.MINIO_ENDPOINT and settings.MINIO_ACCESS_KEY and settings.MINIO_SECRET_KEY)

    def _get_minio_client(self):
        if self._minio_client is not None:
            return self._minio_client

        from minio import Minio

        # Aceita MINIO_ENDPOINT com ou sem protocolo
        endpoint = (settings.MINIO_ENDPOINT or "").replace("http://", "").replace("https://", "").rstrip("/")
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
            # Leitura pública para que as imagens possam ser buscadas direto pelo navegador
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
                logger.warning("Não foi possível definir a policy do bucket %s: %s", bucket_name, e)

    def _put_minio(self, object_key: str, content: bytes, content_type: str) -> None:
        client = self._get_minio_client()
        bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists(client, bucket_name)
        client.put_object(
            bucket_name=bucket_name,
            object_name=object_key,
            data=BytesIO(content),
            length=len(content),
            content_type=content_type,
        )

    def _get_minio(self, object_key: str) -> Tuple[bytes, str]:
        client = self._get_minio_client()
        response = client.get_object(settings.MINIO_BUCKET_NAME, object_key)
        try:
            data = response.read()
            content_type = response.headers.get("Content-Type") or "application/octet-stream"
        finally:
            response.close()
            response.release_conn()
        return data, content_type

    async def upload_image(self, file: UploadFile, folder: str = "logos") -> str:
        """Valida (tamanho e conteúdo real) e grava uma imagem. Retorna a URL pública."""
        max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
        content = await file.read(max_bytes + 1)
        if len(content) > max_bytes:
            raise ValueError(f"A imagem deve ter no máximo {settings.MAX_UPLOAD_MB} MB.")
        detected = _detect_image(content)
        if not detected:
            raise ValueError("Formato não suportado. Envie uma imagem PNG, JPG, WEBP ou GIF.")
        ext, content_type = detected
        return await self._store(content, folder, ext, content_type)

    async def _store(self, content: bytes, folder: str, ext: str, content_type: str) -> str:
        unique_name = f"{uuid.uuid4().hex}{ext}"
        object_key = f"{folder}/{unique_name}"

        if self._is_minio_configured():
            try:
                await run_in_threadpool(self._put_minio, object_key, content, content_type)
                if settings.MINIO_PUBLIC_URL:
                    return f"{settings.MINIO_PUBLIC_URL.rstrip('/')}/{settings.MINIO_BUCKET_NAME}/{object_key}"
                return f"/uploads/{object_key}"
            except Exception as e:
                logger.error("Falha no upload para o MinIO (%s); usando disco local.", e)

        target_dir = os.path.join("uploads", folder)
        os.makedirs(target_dir, exist_ok=True)
        with open(os.path.join(target_dir, unique_name), "wb") as f:
            f.write(content)
        return f"/uploads/{object_key}"

    def is_own_url(self, url: str) -> bool:
        """True se a URL aponta para um arquivo gravado por este serviço."""
        if url.startswith("/uploads/"):
            return True
        if settings.MINIO_PUBLIC_URL:
            prefix = f"{settings.MINIO_PUBLIC_URL.rstrip('/')}/{settings.MINIO_BUCKET_NAME}/"
            return url.startswith(prefix)
        return False

    def object_key_from_url(self, url: str) -> Optional[str]:
        if url.startswith("/uploads/"):
            return url[len("/uploads/"):]
        if settings.MINIO_PUBLIC_URL:
            prefix = f"{settings.MINIO_PUBLIC_URL.rstrip('/')}/{settings.MINIO_BUCKET_NAME}/"
            if url.startswith(prefix):
                return url[len(prefix):]
        return None

    async def get_file_content(self, object_key: str) -> Tuple[Optional[bytes], Optional[str]]:
        """Lê um arquivo do disco local ou do MinIO. Retorna (None, None) se não existir."""
        object_key = os.path.normpath(object_key).replace("\\", "/").lstrip("/")
        if object_key.startswith(".."):
            return None, None

        local_path = os.path.join("uploads", object_key)
        if os.path.isfile(local_path):
            content_type, _ = mimetypes.guess_type(local_path)
            with open(local_path, "rb") as f:
                return f.read(), content_type or "application/octet-stream"

        if self._is_minio_configured():
            try:
                return await run_in_threadpool(self._get_minio, object_key)
            except Exception as e:
                logger.warning("Arquivo '%s' não encontrado no MinIO: %s", object_key, e)

        return None, None

    async def get_data_uri(self, url: Optional[str]) -> Optional[str]:
        """Converte uma URL de arquivo próprio em data URI (usado para embutir a logo no PDF)."""
        if not url or not self.is_own_url(url):
            return None
        key = self.object_key_from_url(url)
        if not key:
            return None
        content, content_type = await self.get_file_content(key)
        if not content or not (content_type or "").startswith("image/") or content_type == "image/svg+xml":
            return None
        import base64
        return f"data:{content_type};base64,{base64.b64encode(content).decode()}"


storage_service = StorageService()
