"""SQLite storage for Avvikelserapportering.

The database file and uploaded attachments live under %LOCALAPPDATA%, not inside
the OneDrive-synced repo folder. OneDrive's file locking/syncing does not play
well with a live SQLite file (same lesson learned in FackverksmastCalc's venv
placement) - only source code lives in OneDrive.
"""

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

APP_DIR_NAME = "Avvikelserapportering"

DEFAULT_ORGANIZATIONS = [
    ("PMF-BERGUM", "PMF-Bergum"),
    ("PMF-VEENDAM", "PMF-Veendam"),
    ("BRASOV", "Brasov"),
]

DEFAULT_DEPARTMENTS = ["Svets", "Montering", "Kapning", "Sälj", "Inköp", "Ekonomi"]

DEFAULT_STATS_PIN = "2026"

SCHEMA = """
CREATE TABLE IF NOT EXISTS organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_no TEXT UNIQUE,
    type TEXT NOT NULL,
    subtype TEXT,
    title TEXT NOT NULL,
    description TEXT,
    organization_id INTEGER NOT NULL,
    department_id INTEGER NOT NULL,
    reporter_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL,
    closed_at TEXT,
    language TEXT,
    FOREIGN KEY (organization_id) REFERENCES organizations(id),
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    content_type TEXT,
    kind TEXT NOT NULL,
    uploaded_at TEXT NOT NULL,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id)
);

CREATE TABLE IF NOT EXISTS updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    author TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id)
);
"""


def _data_dir() -> Path:
    # Explicit override (used on Linux hosts like Render, where there is no
    # %LOCALAPPDATA%) takes priority. Falls back to the Windows-local-data
    # location used for normal desktop runs, and finally to a plain ./data
    # folder for any other environment.
    override = os.environ.get("AVVIKELSER_DATA_DIR")
    if override:
        d = Path(override)
    elif os.environ.get("LOCALAPPDATA"):
        d = Path(os.environ["LOCALAPPDATA"]) / APP_DIR_NAME / "data"
    else:
        d = Path(__file__).resolve().parent.parent / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


DATA_DIR = _data_dir()
DB_PATH = DATA_DIR / "avvikelser.db"
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
_PIN_FILE = DATA_DIR / "stats_pin.txt"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_conn()
    try:
        conn.executescript(SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM organizations").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO organizations (code, name) VALUES (?, ?)",
                DEFAULT_ORGANIZATIONS,
            )
        if conn.execute("SELECT COUNT(*) FROM departments").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO departments (name) VALUES (?)",
                [(d,) for d in DEFAULT_DEPARTMENTS],
            )
        conn.commit()
    finally:
        conn.close()
    if not _PIN_FILE.exists():
        _PIN_FILE.write_text(DEFAULT_STATS_PIN, encoding="utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_stats_pin() -> str:
    try:
        return _PIN_FILE.read_text(encoding="utf-8").strip() or DEFAULT_STATS_PIN
    except OSError:
        return DEFAULT_STATS_PIN
