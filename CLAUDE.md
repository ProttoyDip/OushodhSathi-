Read AGENTS.md and DESIGN.md first. They are the source of truth.

## Commands

Backend (from `/backend`):
- Install: `python -m venv .venv && .venv/Scripts/pip install -r requirements.txt` (Windows) or `.venv/bin/pip` (macOS/Linux)
- Seed demo household: `.venv/Scripts/python scripts/seed_demo.py`
- Run API: `.venv/Scripts/uvicorn app.main:app --reload --port 8000` (docs at http://localhost:8000/docs)
- Tests: `.venv/Scripts/python -m pytest`

Frontend (from `/frontend`):
- `npm install`, `npm run dev` (http://localhost:3000)
- Before commit: `npm run lint && npm run build`

Eval: `backend/.venv/Scripts/python eval/run_eval.py`
