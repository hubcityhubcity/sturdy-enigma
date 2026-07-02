from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import httpx

from local_storage import ORIGINALS_DIR, ensure_dirs

ALLOWED_CONTENT_TYPES = (
    "video/",
    "audio/",
    "application/octet-stream",
)

MAX_DOWNLOAD_BYTES = 2_000_000_000


def extension_from_url(url: str) -> str:
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix and len(suffix) <= 12:
        return suffix
    return ".media"


def is_allowed_content_type(content_type: str | None) -> bool:
    if not content_type:
        return True
    clean = content_type.lower().split(";", 1)[0].strip()
    return any(clean.startswith(prefix) for prefix in ALLOWED_CONTENT_TYPES)


def build_link_path(project_id: str, url: str) -> Path:
    ensure_dirs()
    folder = ORIGINALS_DIR / project_id
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{uuid4()}{extension_from_url(url)}"


def import_direct_media_url(project_id: str, url: str) -> tuple[Path | None, str, str]:
    """Download a direct media URL into local original storage.

    This intentionally supports direct media files only. Platform-specific imports
    should be added later through provider adapters.
    """
    destination = build_link_path(project_id, url)

    try:
        with httpx.stream("GET", url, follow_redirects=True, timeout=60.0) as response:
            response.raise_for_status()
            content_type = response.headers.get("content-type")
            if not is_allowed_content_type(content_type):
                return None, "unsupported_content_type", f"Unsupported content type: {content_type}"

            downloaded = 0
            with destination.open("wb") as output_file:
                for chunk in response.iter_bytes():
                    if not chunk:
                        continue
                    downloaded += len(chunk)
                    if downloaded > MAX_DOWNLOAD_BYTES:
                        destination.unlink(missing_ok=True)
                        return None, "file_too_large", "Downloaded file exceeded the MVP size limit."
                    output_file.write(chunk)

    except httpx.HTTPStatusError as error:
        return None, "download_http_error", f"Download failed with HTTP status {error.response.status_code}."
    except httpx.RequestError as error:
        return None, "download_request_error", f"Download failed: {error}"

    return destination, "downloaded", "Direct media URL downloaded successfully."
