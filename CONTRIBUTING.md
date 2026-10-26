# Contributing

Thank you for helping. OushodhSathi handles medicine-safety findings for elderly patients, so a
few rules matter more than speed.

1. **Read [`AGENTS.md`](AGENTS.md) and [`DESIGN.md`](DESIGN.md) first.** They are the source of
   truth for people and coding agents alike. The six safety rules in `AGENTS.md` are
   non-negotiable: findings come only from the rules engine, families see only confirmed
   findings, and no text ever tells a patient to stop, start or change a medicine.
2. **Run the checks before every commit.**

   ```bash
   cd backend && .venv/bin/python -m pytest
   cd frontend && npm run lint && npm run build
   ```

   CI runs the same checks on every push and pull request.
3. **Changing a safety rule?** Add or update a test in `backend/tests/` that shows the new
   behaviour, and say in the pull request which clinical source supports it.
4. **Changing an LLM prompt?** Add a new version file (`backend/app/prompts/<name>.v<N+1>.md`)
   rather than editing the old one, and re-run `eval/run_eval.py`.
5. **Changing the UI?** Follow `DESIGN.md`, check the screen at 390 px and 1440 px wide in light
   and dark, and keep every number on screen real or labelled as demo data.
6. **Never commit secrets or real patient data.** API keys live only in `backend/.env`. Photos
   used for evaluation must have identifying details removed.

Keep commits small, with messages that say what changed and why.
