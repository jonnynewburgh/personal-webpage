import os
import asyncio
import zipfile
from pathlib import Path
import httpx
from models.schemas import DatasetResult
from .base import DataSource
from config import KAGGLE_USERNAME, KAGGLE_KEY, TMP_DIR

KAGGLE_API_BASE = "https://www.kaggle.com/api/v1"


def _kaggle_configured() -> bool:
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    return bool(
        (KAGGLE_USERNAME and KAGGLE_KEY) or kaggle_json.exists()
    )


def _auth() -> tuple[str, str]:
    if KAGGLE_USERNAME and KAGGLE_KEY:
        return KAGGLE_USERNAME, KAGGLE_KEY
    import json
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    creds = json.loads(kaggle_json.read_text())
    return creds["username"], creds["key"]


class KaggleSource(DataSource):
    async def search(self, query: str, limit: int = 20) -> list[DatasetResult]:
        if not _kaggle_configured():
            raise ValueError("kaggle_not_configured")

        username, key = _auth()
        params = {"search": query, "page": 1, "pageSize": limit}

        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                f"{KAGGLE_API_BASE}/datasets/list",
                params=params,
                auth=(username, key),
            )
            resp.raise_for_status()
            items = resp.json()

        results = []
        for item in items:
            ref = item.get("ref", "")  # "owner/dataset-slug"
            results.append(
                DatasetResult(
                    id=ref,
                    title=item.get("title", ref),
                    description=(item.get("subtitle") or item.get("description") or "")[:300],
                    source_type="kaggle",
                    download_url=f"https://www.kaggle.com/datasets/{ref}",
                    file_format=None,
                )
            )
        return results


async def download_kaggle_dataset(dataset_ref: str) -> tuple[bytes, str]:
    """
    Download a Kaggle dataset zip and return (raw_bytes, file_format)
    for the largest CSV or Parquet file inside.
    """
    if not _kaggle_configured():
        raise ValueError("kaggle_not_configured")

    username, key = _auth()
    owner, slug = dataset_ref.split("/", 1)
    url = f"{KAGGLE_API_BASE}/datasets/{owner}/{slug}/download"

    zip_path = TMP_DIR / f"{slug}.zip"

    async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
        async with client.stream("GET", url, auth=(username, key)) as resp:
            resp.raise_for_status()
            with open(zip_path, "wb") as f:
                async for chunk in resp.aiter_bytes(65536):
                    f.write(chunk)

    extract_dir = TMP_DIR / f"{slug}_extracted"
    extract_dir.mkdir(exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)

    # Find the largest CSV or Parquet file
    candidates = list(extract_dir.rglob("*.csv")) + list(extract_dir.rglob("*.parquet"))
    if not candidates:
        candidates = list(extract_dir.rglob("*"))
    if not candidates:
        raise ValueError("No data files found in Kaggle dataset zip")

    best = max(candidates, key=lambda p: p.stat().st_size)
    ext = best.suffix.lstrip(".").lower()
    if ext not in ("csv", "parquet", "json", "xlsx", "xls"):
        ext = "csv"

    raw = best.read_bytes()

    # Cleanup
    zip_path.unlink(missing_ok=True)
    import shutil
    shutil.rmtree(extract_dir, ignore_errors=True)

    return raw, ext
