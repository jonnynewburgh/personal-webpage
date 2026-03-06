import asyncio
import uuid
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse
from models.schemas import DownloadRequest
from services.sources.url_download import fetch_url
from services.sources.kaggle_source import download_kaggle_dataset
from services.sources.html_scraper import fetch_html_table
from services.ingestor import parse_to_dataframe
from services.db import store_dataframe, sanitize_table_name
from config import JOB_TTL_SECONDS

router = APIRouter()

# job_id → asyncio.Queue of progress dicts
job_registry: dict[str, asyncio.Queue] = {}


async def _cleanup_job(job_id: str, delay: int) -> None:
    await asyncio.sleep(delay)
    job_registry.pop(job_id, None)


async def _run_download(job_id: str, req: DownloadRequest) -> None:
    q = job_registry[job_id]

    async def emit(phase: str, percent: int, message: str):
        await q.put({"phase": phase, "percent": percent, "message": message})

    try:
        # ── FETCH ──────────────────────────────────────────────
        await emit("fetching", 10, "Starting download...")

        if req.source_type == "kaggle":
            if not req.dataset_id:
                raise ValueError("dataset_id required for Kaggle downloads")
            raw, fmt = await download_kaggle_dataset(req.dataset_id)
            await emit("fetching", 40, f"Downloaded Kaggle dataset ({len(raw)//1024} KB)")

        elif req.source_type == "html_table":
            html = await fetch_html_table(req.download_url, req.table_index or 0)
            raw, fmt = html, "html"
            await emit("fetching", 40, "Fetched HTML page")

        else:
            raw, fmt = await fetch_url(req.download_url, q, req.file_format)
            await emit("fetching", 40, f"Downloaded {len(raw)//1024} KB")

        # ── PARSE ──────────────────────────────────────────────
        await emit("parsing", 50, f"Parsing {fmt.upper()} data...")
        df = parse_to_dataframe(raw, fmt, req.table_index or 0)
        await emit("parsing", 65, f"Parsed {len(df):,} rows × {len(df.columns)} columns")

        # ── STORE ──────────────────────────────────────────────
        safe = sanitize_table_name(req.table_name)
        await emit("storing", 75, f"Writing to SQLite table '{safe}'...")
        row_count = await store_dataframe(df, req.table_name)
        await emit("done", 100, f"Done! '{safe}' has {row_count:,} rows.")

    except ValueError as e:
        await emit("error", 0, str(e))
    except Exception as e:
        await emit("error", 0, f"Unexpected error: {e}")
    finally:
        # Signal stream to close
        await q.put(None)


class StartResponse:
    def __init__(self, job_id: str):
        self.job_id = job_id


@router.post("")
async def start_download(req: DownloadRequest):
    job_id = uuid.uuid4().hex
    q: asyncio.Queue = asyncio.Queue()
    job_registry[job_id] = q

    asyncio.create_task(_run_download(job_id, req))
    asyncio.create_task(_cleanup_job(job_id, JOB_TTL_SECONDS))

    return {"job_id": job_id}


@router.get("/progress/{job_id}")
async def stream_progress(job_id: str):
    if job_id not in job_registry:
        raise HTTPException(status_code=404, detail="Job not found")

    q = job_registry[job_id]

    async def event_generator():
        while True:
            item = await q.get()
            if item is None:
                break
            import json
            yield {"data": json.dumps(item)}

    return EventSourceResponse(event_generator())
