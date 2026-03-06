import asyncio
import httpx
from models.schemas import DatasetResult
from .base import DataSource

DATAGOV_API = "https://catalog.data.gov/api/3/action/package_search"

# Prefer these resource formats
PREFERRED_FORMATS = {"CSV", "JSON", "PARQUET", "XLS", "XLSX"}


def _pick_resource(resources: list[dict]) -> tuple[str, str | None]:
    """Return (download_url, file_format) from a dataset's resource list."""
    for fmt in ("CSV", "JSON", "PARQUET", "XLSX", "XLS"):
        for r in resources:
            if r.get("format", "").upper() == fmt and r.get("url"):
                return r["url"], fmt.lower()
    # fallback: first resource with a URL
    for r in resources:
        if r.get("url"):
            return r["url"], r.get("format", "").lower() or None
    return "", None


class DataGovSource(DataSource):
    async def search(self, query: str, limit: int = 20) -> list[DatasetResult]:
        params = {"q": query, "rows": limit, "sort": "score desc"}
        results: list[DatasetResult] = []

        async with httpx.AsyncClient(timeout=20) as client:
            try:
                resp = await client.get(DATAGOV_API, params=params)
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                return []

        for pkg in data.get("result", {}).get("results", []):
            resources = pkg.get("resources", [])
            url, fmt = _pick_resource(resources)
            if not url:
                continue
            results.append(
                DatasetResult(
                    id=pkg.get("id", ""),
                    title=pkg.get("title", "(no title)"),
                    description=(pkg.get("notes") or "")[:300],
                    source_type="datagov",
                    download_url=url,
                    file_format=fmt,
                )
            )

        return results
