from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import db
from .routers import meta, stats, tickets

db.init_db()

app = FastAPI(title="Avvikelserapportering")

app.include_router(meta.router, prefix="/api")
app.include_router(tickets.router, prefix="/api")
app.include_router(stats.router, prefix="/api")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
