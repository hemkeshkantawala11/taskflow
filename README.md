# TaskFlow

A small shared task list: add tasks, tick them off, delete them.
Built with FastAPI (Python) and PostgreSQL, with a plain HTML/JS front end.

## Run locally

1. Start PostgreSQL and create a database called `taskflow`.
2. Install dependencies and run the app:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/taskflow
uvicorn app.main:app --reload
```

3. Open http://localhost:8000

## API

| Method | Path | Body | Purpose |
|---|---|---|---|
| GET | `/api/tasks` | | List tasks |
| POST | `/api/tasks` | `{"title": "..."}` | Create a task |
| PATCH | `/api/tasks/{id}` | `{"done": true}` | Mark done / not done |
| DELETE | `/api/tasks/{id}` | | Delete a task |
