from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from models.schemas import DatasetResult, UrlProbeResult
from services.sources.datagov import DataGovSource
from services.sources.kaggle_source import KaggleSource
from services.sources.html_scraper import probe_html_tables
from services.sources.url_download import probe_url

router = APIRouter()

_datagov = DataGovSource()
_kaggle = KaggleSource()


@router.get("/datagov", response_model=list[DatasetResult])
async def search_datagov(q: str = Query(..., min_length=1), limit: int = Query(20, le=100)):
    return await _datagov.search(q, limit)


@router.get("/kaggle", response_model=list[DatasetResult])
async def search_kaggle(q: str = Query(..., min_length=1), limit: int = Query(20, le=100)):
    try:
        return await _kaggle.search(q, limit)
    except ValueError as e:
        if "kaggle_not_configured" in str(e):
            raise HTTPException(
                status_code=424,
                detail={
                    "error": "kaggle_not_configured",
                    "message": (
                        "Kaggle credentials not found. Set KAGGLE_USERNAME and KAGGLE_KEY "
                        "in your .env file, or place kaggle.json in ~/.kaggle/kaggle.json. "
                        "Get your API key at https://www.kaggle.com/account"
                    ),
                },
            )
        raise HTTPException(status_code=500, detail=str(e))


class UrlProbeRequest(BaseModel):
    url: str


@router.post("/url", response_model=UrlProbeResult)
async def probe_url_endpoint(body: UrlProbeRequest):
    info = await probe_url(body.url)
    if info["detected_type"] == "html":
        try:
            return await probe_html_tables(body.url)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to scrape HTML: {e}")
    return UrlProbeResult(url=body.url, detected_type=info["detected_type"])
