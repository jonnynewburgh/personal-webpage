import io
from pathlib import Path
import pandas as pd


def detect_format_from_path(path: str) -> str:
    p = path.lower().split("?")[0]
    if p.endswith(".csv"):
        return "csv"
    if p.endswith(".parquet"):
        return "parquet"
    if p.endswith((".xls", ".xlsx")):
        return "xlsx"
    if p.endswith(".json"):
        return "json"
    return "unknown"


def parse_to_dataframe(raw: bytes, file_format: str, table_index: int = 0) -> pd.DataFrame:
    buf = io.BytesIO(raw)

    if file_format == "csv":
        return _read_csv(buf)
    if file_format == "parquet":
        return pd.read_parquet(buf)
    if file_format in ("xls", "xlsx"):
        return pd.read_excel(buf, engine="openpyxl")
    if file_format == "json":
        return _read_json(buf)
    if file_format == "html":
        return _read_html(raw, table_index)

    # Last-ditch effort: try CSV
    try:
        return _read_csv(io.BytesIO(raw))
    except Exception:
        pass
    raise ValueError(f"Cannot parse file with format '{file_format}'")


def parse_file_to_dataframe(path: Path, file_format: str) -> pd.DataFrame:
    with open(path, "rb") as f:
        raw = f.read()
    return parse_to_dataframe(raw, file_format)


def _read_csv(buf: io.BytesIO) -> pd.DataFrame:
    # Try common encodings
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            buf.seek(0)
            return pd.read_csv(buf, encoding=enc, low_memory=False)
        except UnicodeDecodeError:
            continue
    buf.seek(0)
    return pd.read_csv(buf, encoding="utf-8", errors="replace", low_memory=False)


def _read_json(buf: io.BytesIO) -> pd.DataFrame:
    buf.seek(0)
    try:
        df = pd.read_json(buf)
        # If result is a single column, it's likely misoriented
        if df.shape[1] == 1:
            buf.seek(0)
            df = pd.read_json(buf, orient="records")
        return df
    except Exception:
        buf.seek(0)
        return pd.read_json(buf, orient="records")


def _read_html(raw: bytes, table_index: int) -> pd.DataFrame:
    tables = pd.read_html(io.BytesIO(raw))
    if not tables:
        raise ValueError("No HTML tables found in page")
    if table_index >= len(tables):
        raise ValueError(f"Table index {table_index} out of range (found {len(tables)})")
    return tables[table_index]
