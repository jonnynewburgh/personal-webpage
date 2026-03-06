from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from routers import search, download, tables
from services.db import init_db

app = FastAPI(title="Personal Data Tool")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(download.router, prefix="/api/download", tags=["download"])
app.include_router(tables.router, prefix="/api/tables", tags=["tables"])


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
