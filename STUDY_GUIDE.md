# Study guide - interview questions this project prepares you for

Read this alongside the code. Every answer points at the file where you can
see the idea working.

## Backend design

**Q: What is the Flask app factory pattern and why use it?**
The app is created inside a function (`create_app` in `app/__init__.py`)
instead of at module level. That means tests can build their own app
instance with a temporary database instead of touching the real one - see
how `tests/test_api.py` gets an isolated app per test. It also keeps config
out of import time, which matters once you have dev/test/prod settings.

**Q: What is a Blueprint?**
`app/routes.py` groups all routes in a `Blueprint("main", ...)` that the
factory registers. Blueprints keep route definitions out of the app object,
so a growing project splits routes by feature instead of one giant file.

**Q: How do you prevent SQL injection here?**
Every query uses parameter placeholders (`?`) with values passed separately
(`db.execute("INSERT INTO projects (name) VALUES (?)", (name,))`), never
f-strings or string concatenation with user input. SQLite then treats the
input as data, not SQL.

## Data modelling

**Q: Why `ON DELETE CASCADE` on tasks.project_id?**
A task cannot exist without its project. The foreign key with cascade
(`app/schema.sql`) makes deleting a project delete its tasks in the same
statement - no orphaned rows, no cleanup loop in Python.

**Q: Why enforce `CHECK (status IN ('todo','doing','done'))` in SQL when
the API validates too?**
Defence in depth. The API validation (`STATUSES` in `app/routes.py`) gives a
friendly 400; the database CHECK is the last line if any other code path
ever writes to the table. Constraints that live in the schema protect the
data no matter which client connects.

**Q: Why the index on tasks(project_id)?**
Almost every task query filters by project (`WHERE t.project_id = ?` in the
board and counts queries). Without the index SQLite scans the whole tasks
table each time. On small data you would never notice; the habit matters.

## API details

**Q: How does the API reject malformed input?**
Three layers in `app/routes.py`: `json_object()` only accepts a JSON object
(not arrays/scalars/garbage), type checks like `isinstance(name, str)`,
then value checks (non-empty after strip, priority in 1-3). Each failure
returns a consistent `{"error": ...}` body with a 400.

**Q: `valid_priority` rejects `True` even though `True == 1` in Python -
why?**
`bool` is a subclass of `int`, so `isinstance(True, int)` passes. Accepting
`true` as priority 1 in a JSON API is a silent data-corruption bug; the
explicit `type(value) is int` check is the kind of detail interviewers
like to hear you noticed.

**Q: How do the project progress counts work in one query?**
`list_projects` uses a `LEFT JOIN` plus `COUNT(t.id)` and
`SUM(t.status = 'done')`, grouped by project. LEFT JOIN (not INNER) so a
project with zero tasks still appears with 0/0 instead of disappearing.

## Testing

**Q: What do the API tests actually prove?**
`tests/test_api.py` exercises the HTTP surface against a temporary
database: create/list/update/delete, validation failures returning 400,
and cascade behaviour. They test through the API contract, not internal
functions, so refactors that keep the contract stay green.

## Full-stack

**Q: How does the frontend talk to the backend?**
`app/static/app.js` uses the browser `fetch` API against the same-origin
`/api/...` endpoints and re-renders the three columns from the JSON - no
framework, no build step. Trade-off: fine at this size, and it shows you
understand what React would be doing for you.
