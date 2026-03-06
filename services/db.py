import re
import uuid
import asyncio
from typing import AsyncGenerator
import aiosqlite
import pandas as pd
from config import DB_PATH
from models.schemas import TableInfo, TablePreview


def sanitize_table_name(raw: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9_]", "_", raw).strip("_").lower()
    if not name:
        name = "table"
    if name[0].isdigit():
        name = "t_" + name
    return name[:64]


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA busy_timeout=5000")
        await conn.commit()


async def store_dataframe(df: pd.DataFrame, table_name: str) -> int:
    """Atomically write a DataFrame into SQLite as table_name."""
    safe_name = sanitize_table_name(table_name)
    tmp_name = f"tmp_{uuid.uuid4().hex}"

    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA busy_timeout=5000")

        # Build CREATE TABLE statement from DataFrame dtypes
        col_defs = []
        for col, dtype in zip(df.columns, df.dtypes):
            safe_col = sanitize_table_name(str(col)) or "col"
            if pd.api.types.is_integer_dtype(dtype):
                sql_type = "INTEGER"
            elif pd.api.types.is_float_dtype(dtype):
                sql_type = "REAL"
            else:
                sql_type = "TEXT"
            col_defs.append(f'"{safe_col}" {sql_type}')

        await conn.execute(
            f'CREATE TABLE "{tmp_name}" ({", ".join(col_defs)})'
        )

        # Rename columns to safe names for insertion
        safe_cols = [sanitize_table_name(str(c)) or "col" for c in df.columns]
        df = df.copy()
        df.columns = safe_cols

        # Insert rows in batches of 1000
        placeholders = ", ".join("?" * len(safe_cols))
        col_names = ", ".join(f'"{c}"' for c in safe_cols)
        insert_sql = f'INSERT INTO "{tmp_name}" ({col_names}) VALUES ({placeholders})'

        rows = [
            [None if pd.isna(v) else v for v in row]
            for row in df.itertuples(index=False, name=None)
        ]
        await conn.executemany(insert_sql, rows)

        # Drop existing table with target name and atomically rename
        await conn.execute(f'DROP TABLE IF EXISTS "{safe_name}"')
        await conn.execute(f'ALTER TABLE "{tmp_name}" RENAME TO "{safe_name}"')
        await conn.commit()

    return len(df)


async def list_tables() -> list[TableInfo]:
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("PRAGMA journal_mode=WAL")
        cursor = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'tmp_%' ORDER BY name"
        )
        table_names = [row[0] for row in await cursor.fetchall()]

        results = []
        for name in table_names:
            count_cur = await conn.execute(f'SELECT COUNT(*) FROM "{name}"')
            row_count = (await count_cur.fetchone())[0]

            info_cur = await conn.execute(f'PRAGMA table_info("{name}")')
            columns = [row[1] for row in await info_cur.fetchall()]

            results.append(TableInfo(name=name, row_count=row_count, columns=columns))

    return results


async def preview_table(table_name: str, rows: int = 50) -> TablePreview:
    safe_name = sanitize_table_name(table_name)
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("PRAGMA journal_mode=WAL")
        cursor = await conn.execute(f'SELECT * FROM "{safe_name}" LIMIT {rows}')
        columns = [desc[0] for desc in cursor.description]
        data = await cursor.fetchall()

    return TablePreview(columns=columns, rows=[list(r) for r in data])


async def drop_table(table_name: str) -> None:
    safe_name = sanitize_table_name(table_name)
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(f'DROP TABLE IF EXISTS "{safe_name}"')
        await conn.commit()
