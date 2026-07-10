from fastapi import APIRouter, Form, HTTPException

from .. import db

router = APIRouter(tags=["meta"])

LANGUAGES = [
    {"code": "nl", "label": "Nederlands"},
    {"code": "en", "label": "English"},
    {"code": "ro", "label": "Română"},
    {"code": "sv", "label": "Svenska"},
    {"code": "no", "label": "Norsk"},
]


@router.get("/meta")
def get_meta():
    conn = db.get_conn()
    try:
        orgs = [dict(r) for r in conn.execute("SELECT id, code, name FROM organizations ORDER BY name")]
        departments = [
            dict(r)
            for r in conn.execute(
                "SELECT id, name FROM departments WHERE active = 1 ORDER BY name"
            )
        ]
    finally:
        conn.close()
    return {"organizations": orgs, "departments": departments, "languages": LANGUAGES}


@router.post("/departments")
def add_department(name: str = Form(...)):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    conn = db.get_conn()
    try:
        existing = conn.execute(
            "SELECT id, active FROM departments WHERE name = ?", (name,)
        ).fetchone()
        if existing:
            if not existing["active"]:
                conn.execute("UPDATE departments SET active = 1 WHERE id = ?", (existing["id"],))
                conn.commit()
        else:
            conn.execute("INSERT INTO departments (name) VALUES (?)", (name,))
            conn.commit()
        departments = [
            dict(r)
            for r in conn.execute(
                "SELECT id, name FROM departments WHERE active = 1 ORDER BY name"
            )
        ]
    finally:
        conn.close()
    return {"departments": departments}
