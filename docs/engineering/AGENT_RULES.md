# Agent Rules

## Global rules

- Never work directly on `main`.
- Always create a dedicated branch for each task.
- Keep each PR small and reviewable.
- Do not modify unrelated files.
- Preserve existing API response shapes unless the task explicitly allows a breaking change.
- Add or update tests for backend behavior changes.
- Do not commit secrets or `.env`.
- Do not commit generated/local files.

## Never commit

- `.env`
- `backend/.venv`
- `node_modules`
- `dist`
- `backend/storage_db`
- `__pycache__`
- `.pytest_cache`
- `.DS_Store`

## Required validation

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest tests
cd ..
```
