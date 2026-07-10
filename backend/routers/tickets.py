import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from .. import db

router = APIRouter(tags=["tickets"])

VALID_TYPES = {"customer_complaint", "internal"}
VALID_SUBTYPES = {"deviation", "disruption"}
EMAIL_EXTENSIONS = {".eml", ".msg"}


def _classify(filename: str, content_type: Optional[str]) -> str:
    ext = Path(filename).suffix.lower()
    if content_type and content_type.startswith("image/"):
        return "image"
    if ext in EMAIL_EXTENSIONS:
        return "email"
    return "other"


def _row_ticket(row) -> dict:
    d = dict(row)
    return d


def _get_ticket_detail(conn, ticket_id: int) -> dict:
    row = conn.execute(
        """
        SELECT t.*, o.name AS organization_name, o.code AS organization_code,
               dep.name AS department_name
        FROM tickets t
        JOIN organizations o ON o.id = t.organization_id
        JOIN departments dep ON dep.id = t.department_id
        WHERE t.id = ?
        """,
        (ticket_id,),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket = _row_ticket(row)
    ticket["attachments"] = [
        dict(r)
        for r in conn.execute(
            "SELECT id, filename, content_type, kind, uploaded_at FROM attachments WHERE ticket_id = ? ORDER BY uploaded_at",
            (ticket_id,),
        )
    ]
    ticket["updates"] = [
        dict(r)
        for r in conn.execute(
            "SELECT id, author, text, created_at FROM updates WHERE ticket_id = ? ORDER BY created_at",
            (ticket_id,),
        )
    ]
    return ticket


@router.post("/tickets")
async def create_ticket(
    type: str = Form(...),
    subtype: Optional[str] = Form(None),
    title: str = Form(...),
    description: str = Form(""),
    organization_id: int = Form(...),
    department_id: int = Form(...),
    reporter_name: str = Form(...),
    language: Optional[str] = Form(None),
    files: List[UploadFile] = File(default=[]),
):
    if type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail="Invalid type")
    if type == "internal":
        if subtype not in VALID_SUBTYPES:
            raise HTTPException(status_code=400, detail="Invalid subtype for internal ticket")
    else:
        subtype = None
    title = title.strip()
    reporter_name = reporter_name.strip()
    if not title or not reporter_name:
        raise HTTPException(status_code=400, detail="Title and reporter name are required")

    conn = db.get_conn()
    try:
        org = conn.execute("SELECT id FROM organizations WHERE id = ?", (organization_id,)).fetchone()
        dep = conn.execute("SELECT id FROM departments WHERE id = ?", (department_id,)).fetchone()
        if not org or not dep:
            raise HTTPException(status_code=400, detail="Unknown organization or department")

        now = db.now_iso()
        cur = conn.execute(
            """
            INSERT INTO tickets
                (type, subtype, title, description, organization_id, department_id,
                 reporter_name, status, created_at, language)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)
            """,
            (type, subtype, title, description, organization_id, department_id, reporter_name, now, language),
        )
        ticket_id = cur.lastrowid
        ticket_no = f"AV-{ticket_id:05d}"
        conn.execute("UPDATE tickets SET ticket_no = ? WHERE id = ?", (ticket_no, ticket_id))

        for f in files:
            if not f.filename:
                continue
            content = await f.read()
            if not content:
                continue
            ext = Path(f.filename).suffix
            stored_name = f"{uuid.uuid4().hex}{ext}"
            (db.UPLOADS_DIR / stored_name).write_bytes(content)
            kind = _classify(f.filename, f.content_type)
            conn.execute(
                """
                INSERT INTO attachments (ticket_id, filename, stored_path, content_type, kind, uploaded_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (ticket_id, f.filename, stored_name, f.content_type, kind, db.now_iso()),
            )
        conn.commit()
        return _get_ticket_detail(conn, ticket_id)
    finally:
        conn.close()


@router.get("/tickets")
def list_tickets(
    organization_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    clauses = []
    params: list = []
    if organization_id:
        clauses.append("t.organization_id = ?")
        params.append(organization_id)
    if department_id:
        clauses.append("t.department_id = ?")
        params.append(department_id)
    if type:
        clauses.append("t.type = ?")
        params.append(type)
    if status:
        clauses.append("t.status = ?")
        params.append(status)
    if q:
        clauses.append("(t.title LIKE ? OR t.description LIKE ? OR t.reporter_name LIKE ? OR t.ticket_no LIKE ?)")
        like = f"%{q}%"
        params.extend([like, like, like, like])
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    conn = db.get_conn()
    try:
        total = conn.execute(f"SELECT COUNT(*) FROM tickets t {where}", params).fetchone()[0]
        rows = conn.execute(
            f"""
            SELECT t.id, t.ticket_no, t.type, t.subtype, t.title, t.status,
                   t.created_at, t.closed_at, t.reporter_name,
                   o.name AS organization_name, dep.name AS department_name
            FROM tickets t
            JOIN organizations o ON o.id = t.organization_id
            JOIN departments dep ON dep.id = t.department_id
            {where}
            ORDER BY t.created_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        ).fetchall()
        items = [dict(r) for r in rows]
    finally:
        conn.close()
    return {"items": items, "total": total}


@router.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int):
    conn = db.get_conn()
    try:
        return _get_ticket_detail(conn, ticket_id)
    finally:
        conn.close()


@router.post("/tickets/{ticket_id}/updates")
def add_update(ticket_id: int, author: str = Form(...), text: str = Form(...)):
    author = author.strip()
    text = text.strip()
    if not author or not text:
        raise HTTPException(status_code=400, detail="Author and text are required")
    conn = db.get_conn()
    try:
        exists = conn.execute("SELECT id FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Ticket not found")
        conn.execute(
            "INSERT INTO updates (ticket_id, author, text, created_at) VALUES (?, ?, ?, ?)",
            (ticket_id, author, text, db.now_iso()),
        )
        conn.commit()
        return _get_ticket_detail(conn, ticket_id)
    finally:
        conn.close()


@router.post("/tickets/{ticket_id}/close")
def close_ticket(ticket_id: int, author: str = Form(...)):
    conn = db.get_conn()
    try:
        row = conn.execute("SELECT status FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")
        now = db.now_iso()
        conn.execute("UPDATE tickets SET status = 'closed', closed_at = ? WHERE id = ?", (now, ticket_id))
        conn.execute(
            "INSERT INTO updates (ticket_id, author, text, created_at) VALUES (?, ?, ?, ?)",
            (ticket_id, author.strip() or "?", "Ärendet stängt.", now),
        )
        conn.commit()
        return _get_ticket_detail(conn, ticket_id)
    finally:
        conn.close()


@router.post("/tickets/{ticket_id}/reopen")
def reopen_ticket(ticket_id: int, author: str = Form(...)):
    conn = db.get_conn()
    try:
        row = conn.execute("SELECT status FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Ticket not found")
        conn.execute("UPDATE tickets SET status = 'open', closed_at = NULL WHERE id = ?", (ticket_id,))
        conn.execute(
            "INSERT INTO updates (ticket_id, author, text, created_at) VALUES (?, ?, ?, ?)",
            (ticket_id, author.strip() or "?", "Ärendet återöppnat.", db.now_iso()),
        )
        conn.commit()
        return _get_ticket_detail(conn, ticket_id)
    finally:
        conn.close()


@router.get("/tickets/{ticket_id}/attachments/{attachment_id}")
def get_attachment(ticket_id: int, attachment_id: int):
    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT filename, stored_path, content_type FROM attachments WHERE id = ? AND ticket_id = ?",
            (attachment_id, ticket_id),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Attachment not found")
    path = db.UPLOADS_DIR / row["stored_path"]
    if not path.exists():
        raise HTTPException(status_code=404, detail="File missing")
    return FileResponse(path, media_type=row["content_type"] or "application/octet-stream", filename=row["filename"])
