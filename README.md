# TaskBoard

A small full-stack Kanban task tracker: Flask REST API, SQLite database, and a vanilla JavaScript single-page frontend.

## Features
- Projects with progress counts (done/total)
- Tasks with priority (high/medium/low) and optional due date
- Three-column board (To do, In progress, Done), overdue highlighting
- Input validation, foreign keys with cascade delete
- pytest suite for the API

## Stack
| Layer | Tech |
|-------|------|
| Frontend | HTML, CSS, vanilla JS (fetch API) |
| Backend | Python, Flask (blueprint + app factory) |
| Database | SQLite (schema in `app/schema.sql`) |
| Tests | pytest |

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py          # http://127.0.0.1:5000
pytest                 # run the tests
```
Set `TASKBOARD_DB=/path/to/file.db` to change the database location.

## API
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/projects` | List projects with task counts |
| POST | `/api/projects` | `{ "name": "..." }` |
| DELETE | `/api/projects/<id>` | Delete project and its tasks |
| GET | `/api/projects/<id>/tasks?status=todo` | List tasks |
| POST | `/api/projects/<id>/tasks` | `{ "title", "priority"?, "due_date"? }` |
| PATCH | `/api/tasks/<id>` | Update `status`, `title`, `priority` |
| DELETE | `/api/tasks/<id>` | Delete task |

## Structure
```
app/            Flask package (factory, routes, db helpers, schema)
app/static/     CSS and JS
app/templates/  HTML
tests/          API tests
run.py          Entry point
```

## Ideas for extension
User accounts, drag and drop, Docker, Postgres.
