from pydantic import BaseModel
from typing import Literal, Optional, Any


class DatasetResult(BaseModel):
    id: str
    title: str
    description: str
    source_type: Literal["datagov", "kaggle", "url", "html_table"]
    download_url: str
    file_format: Optional[str] = None  # "csv", "json", "parquet", "xlsx"


class HtmlTableCandidate(BaseModel):
    index: int
    rows: int
    cols: int
    headers: list[str]


class UrlProbeResult(BaseModel):
    url: str
    detected_type: str  # "csv", "json", "parquet", "xlsx", "html", "unknown"
    html_tables: Optional[list[HtmlTableCandidate]] = None


class DownloadRequest(BaseModel):
    source_type: Literal["datagov", "kaggle", "url", "html_table"]
    download_url: str
    table_name: str
    dataset_id: Optional[str] = None   # Kaggle: "owner/dataset-slug"
    table_index: Optional[int] = None  # HTML scraping: which <table>
    file_format: Optional[str] = None  # hint for direct URLs


class ProgressEvent(BaseModel):
    phase: Literal["fetching", "parsing", "storing", "done", "error"]
    percent: int
    message: str


class TableInfo(BaseModel):
    name: str
    row_count: int
    columns: list[str]


class TablePreview(BaseModel):
    columns: list[str]
    rows: list[list[Any]]
