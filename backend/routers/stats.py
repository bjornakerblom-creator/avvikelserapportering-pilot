import csv
import io
from typing import Optional

from fastapi import APIRouter, Form, Query
from fastapi.responses import Response

from .. import db

router = APIRouter(tags=["stats"])

TYPE_LABEL_SQL = """
CASE
    WHEN t.type = 'customer_complaint' THEN 'customer_complaint'
    WHEN t.subtype = 'deviation' THEN 'deviation'
    WHEN t.subtype = 'disruption' THEN 'disruption'
    ELSE t.type
END
"""


def _build_filters(organization_id, department_id, type_, status, date_from, date_to):
    clauses = []
    params: list = []
    if organization_id:
        clauses.append("t.organization_id = ?")
        params.append(organization_id)
    if department_id:
        clauses.append("t.department_id = ?")
        params.append(department_id)
    if type_:
        clauses.append("t.type = ?")
        params.append(type_)
    if status:
        clauses.append("t.status = ?")
        params.append(status)
    if date_from:
        clauses.append("t.created_at >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("t.created_at <= ?")
        params.append(date_to + "T23:59:59")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return where, params


@router.post("/stats/auth")
def stats_auth(pin: str = Form(...)):
    return {"ok": pin.strip() == db.get_stats_pin()}


@router.get("/stats")
def get_stats(
    organization_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    where, params = _build_filters(organization_id, department_id, type, status, date_from, date_to)

    conn = db.get_conn()
    try:
        total = conn.execute(f"SELECT COUNT(*) FROM tickets t {where}", params).fetchone()[0]
        open_count = conn.execute(
            f"SELECT COUNT(*) FROM tickets t {where}{' AND' if where else 'WHERE'} t.status = 'open'",
            params,
        ).fetchone()[0]
        closed_count = total - open_count
        avg_row = conn.execute(
            f"""
            SELECT AVG(julianday(t.closed_at) - julianday(t.created_at))
            FROM tickets t {where}{' AND' if where else 'WHERE'} t.status = 'closed'
            """,
            params,
        ).fetchone()[0]
        avg_resolution_days = round(avg_row, 1) if avg_row is not None else None

        by_org = [
            dict(r)
            for r in conn.execute(
                f"""
                SELECT o.name AS label, COUNT(*) AS count
                FROM tickets t JOIN organizations o ON o.id = t.organization_id
                {where}
                GROUP BY o.name ORDER BY count DESC
                """,
                params,
            )
        ]
        by_department = [
            dict(r)
            for r in conn.execute(
                f"""
                SELECT dep.name AS label, COUNT(*) AS count
                FROM tickets t JOIN departments dep ON dep.id = t.department_id
                {where}
                GROUP BY dep.name ORDER BY count DESC
                """,
                params,
            )
        ]
        by_type = [
            dict(r)
            for r in conn.execute(
                f"""
                SELECT {TYPE_LABEL_SQL} AS label, COUNT(*) AS count
                FROM tickets t
                {where}
                GROUP BY label ORDER BY count DESC
                """,
                params,
            )
        ]
        timeseries = [
            dict(r)
            for r in conn.execute(
                f"""
                SELECT substr(t.created_at, 1, 7) AS period, COUNT(*) AS count
                FROM tickets t
                {where}
                GROUP BY period ORDER BY period
                """,
                params,
            )
        ]
    finally:
        conn.close()

    return {
        "total": total,
        "open": open_count,
        "closed": closed_count,
        "avg_resolution_days": avg_resolution_days,
        "by_organization": by_org,
        "by_department": by_department,
        "by_type": by_type,
        "timeseries": timeseries,
    }


@router.get("/stats/export.csv")
def export_csv(
    organization_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    where, params = _build_filters(organization_id, department_id, type, status, date_from, date_to)
    conn = db.get_conn()
    try:
        rows = conn.execute(
            f"""
            SELECT t.ticket_no, t.type, t.subtype, t.title, t.status,
                   o.name AS organization, dep.name AS department,
                   t.reporter_name, t.created_at, t.closed_at
            FROM tickets t
            JOIN organizations o ON o.id = t.organization_id
            JOIN departments dep ON dep.id = t.department_id
            {where}
            ORDER BY t.created_at DESC
            """,
            params,
        ).fetchall()
    finally:
        conn.close()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["ticket_no", "type", "subtype", "title", "status", "organization", "department", "reporter_name", "created_at", "closed_at"])
    for r in rows:
        writer.writerow(list(r))
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=avvikelser_export.csv"},
    )
