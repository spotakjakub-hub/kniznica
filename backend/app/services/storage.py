"""Cover image storage in Supabase Storage (public bucket "covers")."""
import os
import uuid
from typing import Optional

import httpx

BUCKET = "covers"
_bucket_ready = False


class StorageError(Exception):
    pass


def _config():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise StorageError("SUPABASE_URL / SUPABASE_SERVICE_KEY not configured")
    return url.rstrip("/"), {"Authorization": f"Bearer {key}", "apikey": key}


def _ensure_bucket():
    global _bucket_ready
    if _bucket_ready:
        return
    url, headers = _config()
    r = httpx.post(f"{url}/storage/v1/bucket", headers=headers,
                   json={"id": BUCKET, "name": BUCKET, "public": True}, timeout=15)
    if r.status_code not in (200, 201, 400, 409):  # 400/409 = already exists
        raise StorageError(f"Bucket create failed: HTTP {r.status_code}: {r.text[:200]}")
    _bucket_ready = True


def upload_cover(data: bytes, content_type: Optional[str]) -> str:
    """Uploads an image, returns its public URL."""
    _ensure_bucket()
    url, headers = _config()
    ext = {"image/png": "png", "image/webp": "webp", "image/heic": "heic"}.get(content_type, "jpg")
    path = f"{uuid.uuid4().hex}.{ext}"
    r = httpx.post(
        f"{url}/storage/v1/object/{BUCKET}/{path}",
        headers={**headers, "Content-Type": content_type or "image/jpeg"},
        content=data,
        timeout=60,
    )
    if r.status_code not in (200, 201):
        raise StorageError(f"Upload failed: HTTP {r.status_code}: {r.text[:200]}")
    return f"{url}/storage/v1/object/public/{BUCKET}/{path}"
