import sqlite3
from datetime import date
from flask import Blueprint, jsonify, render_template, request
from .db import get_db

bp = Blueprint("main", __name__)
STATUSES = {"todo", "doing", "done"}


def row(r):
    return dict(r) if r else None


def error(msg, code=400):
    return jsonify(error=msg), code


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/api/projects")
def list_projects():
    rows = get_db().execute(
        """SELECT p.id, p.name,
                  COUNT(t.id) AS total,
                  COALESCE(SUM(t.status = 'done'), 0) AS done
           FROM projects p LEFT JOIN tasks t ON t.project_id = p.id
           GROUP BY p.id ORDER BY p.name"""
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.post("/api/projects")
def create_project():
    name = (request.get_json(silent=True) or {}).get("name", "").strip()
    if not name:
        return error("name is required")
    db = get_db()
    try:
        cur = db.execute("INSERT INTO projects (name) VALUES (?)", (name,))
    except sqlite3.IntegrityError:
        return error("project already exists", 409)
    db.commit()
    return jsonify(id=cur.lastrowid, name=name), 201


@bp.delete("/api/projects/<int:pid>")
def delete_project(pid):
    db = get_db()
    cur = db.execute("DELETE FROM projects WHERE id = ?", (pid,))
    db.commit()
    return ("", 204) if cur.rowcount else error("not found", 404)


@bp.get("/api/projects/<int:pid>/tasks")
def list_tasks(pid):
    status = request.args.get("status")
    sql, args = "SELECT * FROM tasks WHERE project_id = ?", [pid]
    if status:
        if status not in STATUSES:
            return error("invalid status")
        sql += " AND status = ?"
        args.append(status)
    sql += " ORDER BY priority, COALESCE(due_date, '9999-12-31'), id"
    rows = get_db().execute(sql, args).fetchall()
    today = date.today().isoformat()
    out = []
    for r in rows:
        d = dict(r)
        d["overdue"] = bool(d["due_date"] and d["due_date"] < today and d["status"] != "done")
        out.append(d)
    return jsonify(out)


@bp.post("/api/projects/<int:pid>/tasks")
def create_task(pid):
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    priority = data.get("priority", 2)
    due = data.get("due_date") or None
    if not title:
        return error("title is required")
    if priority not in (1, 2, 3):
        return error("priority must be 1, 2 or 3")
    if due:
        try:
            date.fromisoformat(due)
        except ValueError:
            return error("due_date must be YYYY-MM-DD")
    db = get_db()
    if not db.execute("SELECT 1 FROM projects WHERE id = ?", (pid,)).fetchone():
        return error("project not found", 404)
    cur = db.execute(
        "INSERT INTO tasks (project_id, title, priority, due_date) VALUES (?, ?, ?, ?)",
        (pid, title, priority, due),
    )
    db.commit()
    task = db.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(row(task)), 201


@bp.patch("/api/tasks/<int:tid>")
def update_task(tid):
    data = request.get_json(silent=True) or {}
    fields, args = [], []
    if "status" in data:
        if data["status"] not in STATUSES:
            return error("invalid status")
        fields.append("status = ?"); args.append(data["status"])
    if "title" in data:
        if not str(data["title"]).strip():
            return error("title cannot be empty")
        fields.append("title = ?"); args.append(data["title"].strip())
    if "priority" in data:
        if data["priority"] not in (1, 2, 3):
            return error("priority must be 1, 2 or 3")
        fields.append("priority = ?"); args.append(data["priority"])
    if not fields:
        return error("nothing to update")
    db = get_db()
    cur = db.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", (*args, tid))
    db.commit()
    if not cur.rowcount:
        return error("not found", 404)
    return jsonify(row(db.execute("SELECT * FROM tasks WHERE id = ?", (tid,)).fetchone()))


@bp.delete("/api/tasks/<int:tid>")
def delete_task(tid):
    db = get_db()
    cur = db.execute("DELETE FROM tasks WHERE id = ?", (tid,))
    db.commit()
    return ("", 204) if cur.rowcount else error("not found", 404)
