import asyncio
from pathlib import Path
import httpx
import aiofiles
from config import LARGE_FILE_THRESHOLD, TMP_DIR
from services.ingestor import detect_format_from_path


def _detect_format_from_content_type(ct: str) -> str:
    ct = ct.lower()
    if "csv" in ct or "text/plain" in ct:
        return "csv"
    if "json" in ct:
        return "json"
    if "parquet" in ct:
        return "parquet"
    if "excel" in ct or "spreadsheet" in ct or "xls" in ct:
        return "xlsx"
    if "html" in ct:
        return "html"
    return "unknown"


async def fetch_url(
    url: str,
    progress_queue: asyncio.Queue,
    hint_format: str | None = None,
) -> tuple[bytes, str]:
    """Download a URL, streaming it, and return (raw_bytes, file_format)."""
    async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
        async with client.stream("GET", url) as resp:
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            total = int(resp.headers.get("content-length", 0))

            fmt = hint_format
            if not fmt or fmt == "unknown":
                fmt = detect_format_from_path(str(resp.url))
            if not fmt or fmt == "unknown":
                fmt = _detect_format_from_content_type(content_type)

            received = 0
            chunks: list[bytes] = []
            tmp_file = None

            async for chunk in resp.aiter_bytes(65536):
                chunks.append(chunk)
                received += len(chunk)

                if total:
                    pct = int(received / total * 30) + 10
                else:
                    pct = 20

                mb = received / (1024 * 1024)
                await progress_queue.put({
                    "phase": "fetching",
                    "percent": min(pct, 39),
                    "message": f"Downloading... {mb:.1f} MB received",
                })

    raw = b"".join(chunks)
    return raw, fmt


async def probe_url(url: str) -> dict:
    """HEAD + optional GET to detect content type and format."""
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        try:
            head = await client.head(url)
            ct = head.headers.get("content-type", "")
            size = int(head.headers.get("content-length", 0))
        except Exception:
            ct = ""
            size = 0

    fmt = detect_format_from_path(url)
    if not fmt or fmt == "unknown":
        fmt = _detect_format_from_content_type(ct)

    return {"detected_type": fmt, "content_type": ct, "size": size}
