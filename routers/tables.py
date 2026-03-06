from fastapi import APIRouter, HTTPException, Query
from models.schemas import TableInfo, TablePreview
from services.db import list_tables, preview_table, drop_table, sanitize_table_name

router = APIRouter()


@router.get("", response_model=list[TableInfo])
async def get_tables():
    return await list_tables()


@router.get("/{table_name}/preview", response_model=TablePreview)
async def get_preview(table_name: str, rows: int = Query(50, le=500)):
    try:
        return await preview_table(table_name, rows)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{table_name}")
async def delete_table(table_name: str):
    await drop_table(table_name)
    return {"deleted": sanitize_table_name(table_name)}
