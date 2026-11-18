"""Generate docs/API.md (from the FastAPI routes) and docs/CONFIGURATION.md (from backend/.env.example).

  python backend/scripts/gen_docs.py           # write both files
  python backend/scripts/gen_docs.py --check   # exit 1 if either file is out of date (run in the tests)

The reference docs are generated so they cannot drift from the code: every endpoint, who may call it and
its docstring's first line come from the app itself; every setting and its note come from .env.example.
"""
from __future__ import annotations

import argparse
import inspect
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DATABASE_URL", "")

API_MD = ROOT / "docs" / "API.md"
CONFIG_MD = ROOT / "docs" / "CONFIGURATION.md"
ENV_EXAMPLE = ROOT / "backend" / ".env.example"

# first path segment -> section title, in the order they appear in the reference
SECTIONS = [
    ("health", "Service"), ("patients", "Households, medicines and findings"), ("items", "Households, medicines and findings"),
    ("flags", "Reviewer queue and decisions"), ("reviewer", "Reviewer queue and decisions"),
    ("review", "Reviewer queue and decisions"), ("admin", "Administration"), ("assistant", "Sathi (in-app helper)"),
    ("sathi", "Sathi (in-app helper)"), ("calls", "Daily check-in call"), ("whatsapp", "Daily WhatsApp check-in"),
    ("brands", "Brands and research"), ("research", "Brands and research"), ("e", "Emergency page"),
    ("emergency", "Emergency page"), ("eval", "Evaluation (public numbers)"), ("pilot", "Evaluation (public numbers)"),
    ("models", "AI models"), ("demo", "Demo"), ("fhir", "Exports"), ("reports", "Exports"),
]

ACCESS = {
    "require_admin": "admin token", "require_reviewer": "reviewer", "current_reviewer": "reviewer",
    "family_access": "family link", "item_access": "family link",
}


def _access(route) -> str:
    names = {d.call.__name__ for d in route.dependant.dependencies}
    for name in ("require_admin", "require_reviewer", "current_reviewer", "family_access", "item_access"):
        if name in names:
            return ACCESS[name]
    params = inspect.signature(route.endpoint).parameters
    if "x_family_key" in params:
        return "family link"
    if "x_reviewer_token" in params:
        return "reviewer"
    return "public"


def _summary(route) -> str:
    doc = inspect.getdoc(route.endpoint) or ""
    first = re.split(r"(?<=[.!?])\s", " ".join(doc.split()), maxsplit=1)[0] if doc else ""
    return first.replace("|", "\\|")


def api_md() -> str:
    from fastapi.routing import APIRoute

    from app.main import app

    groups: dict[str, list[str]] = {}
    order = list(dict.fromkeys(title for _, title in SECTIONS)) + ["Other"]
    lookup = dict(SECTIONS)
    for r in app.routes:
        if not isinstance(r, APIRoute):
            continue
        seg = r.path.strip("/").split("/")[0]
        title = lookup.get(seg, "Other")
        for method in sorted(r.methods - {"HEAD"}):
            groups.setdefault(title, []).append(f"| `{method}` | `{r.path}` | {_access(r)} | {_summary(r)} |")
    out = [
        "# API reference",
        "",
        "Generated from the FastAPI app by [`backend/scripts/gen_docs.py`](../backend/scripts/gen_docs.py); do not edit by hand.",
        "The interactive version with request and response schemas runs at `/docs` on the API "
        "(for example http://localhost:8000/docs).",
        "",
        "**Who may call it**",
        "",
        "- **public**: anyone (rate limits still apply).",
        "- **family link**: the household's private key in the `X-Family-Key` header (the invented demo household "
        "needs none). A wrong key answers \"not found\", so household ids cannot be probed.",
        "- **reviewer**: a personal reviewer token in `X-Reviewer-Token` (the shared demo token works only when "
        "`DEMO_MODE=true`).",
        "- **admin token**: `ADMIN_TOKEN` in `X-Admin-Token`.",
        "",
        "Webhook routes check the provider's signature themselves.",
        "",
    ]
    total = 0
    for title in order:
        rows = groups.get(title)
        if not rows:
            continue
        total += len(rows)
        out += [f"## {title}", "", "| Method | Path | Who | What it does |", "| --- | --- | --- | --- |", *rows, ""]
    out.insert(3, f"{total} endpoints.")
    out.insert(4, "")
    return "\n".join(out).rstrip() + "\n"


CONFIG_GROUPS = [
    ("AI providers", ("NVIDIA_", "OPENROUTER_", "NARAROUTER_", "EXPLAB_", "AGENTROUTER_", "OLLAMA_", "PERPLEXITY_", "TAVILY_")),
    ("Access, modes and photo privacy", ("REVIEWER_TOKEN", "DEMO_MODE", "ADMIN_TOKEN", "PRIVATE_VISION", "VISION_PROVIDERS")),
    ("Photo reading", ("OCR_CHECK_DISABLED",)),
    ("Notifications", ("RESEND_", "NOTIFY_FROM", "PUBLIC_APP_URL", "N8N_")),
    ("Daily check-in call", ("CALL_PROVIDER", "PUBLIC_API_URL", "PHONE_ENCRYPTION_KEY", "AZURE_SPEECH_")),
    ("Daily WhatsApp check-in", ("WHATSAPP_",)),
    ("Sathi (in-app helper)", ("SATHI_", "EMBEDDINGS_", "HELP_")),
    ("Web, database and rate limits", ("CORS_", "OUSHODH_DB", "DATABASE_URL", "SCAN_LIMIT", "PATIENT_LIMIT", "WRITE_LIMIT", "SATHI_LIMIT")),
]
_LINE = re.compile(r"^([A-Z][A-Z0-9_]*)=([^#]*?)\s*(?:#\s*(.*))?$")


def _env_rows() -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for raw in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        m = _LINE.match(line)
        if m:
            rows.append((m.group(1), m.group(2).strip(), (m.group(3) or "").strip()))
        elif line.strip().startswith("#") and raw[:1].isspace() and rows:  # an indented continuation comment
            name, default, note = rows[-1]
            rows[-1] = (name, default, f"{note} {line.strip().lstrip('#').strip()}".strip())
    return rows


def _group(name: str) -> str:
    # the most specific prefix wins (SATHI_LIMIT_PER_IP is a rate limit, not a Sathi model setting)
    best, length = "Other", 0
    for title, prefixes in CONFIG_GROUPS:
        for p in prefixes:
            if name.startswith(p) and len(p) > length:
                best, length = title, len(p)
    return best


def config_md() -> str:
    groups: dict[str, list[str]] = {}
    for name, default, note in _env_rows():
        secret = any(w in name for w in ("KEY", "TOKEN", "SECRET")) and name not in ("NVIDIA_ASR_FUNCTION_ID",)
        default_txt = f"`{default}`" if default else "unset"
        groups.setdefault(_group(name), []).append(
            f"| `{name}`{' (secret)' if secret else ''} | {default_txt} | {note.replace('|', '\\|')} |")
    out = [
        "# Configuration",
        "",
        "Every setting the API reads, generated from [`backend/.env.example`](../backend/.env.example) by "
        "[`backend/scripts/gen_docs.py`](../backend/scripts/gen_docs.py); do not edit by hand.",
        "",
        "Put values in `backend/.env` locally (never commit it) and in the Render environment when hosted. "
        "With nothing set, everything still runs: `DEMO_MODE=true`, SQLite, fixed templates instead of model "
        "wording, keyword search instead of vectors, and simulators for the check-in call and the WhatsApp message.",
        "Settings marked **secret** are keys or tokens: keep them out of the repository, chats and screenshots.",
        "",
    ]
    for title in [t for t, _ in CONFIG_GROUPS] + ["Other"]:
        rows = groups.get(title)
        if rows:
            out += [f"## {title}", "", "| Setting | Default | What it does |", "| --- | --- | --- |", *rows, ""]
    out += ["The frontend reads `NEXT_PUBLIC_API_URL` (the API's address; required for a production build), "
            "`NEXT_PUBLIC_SITE_URL` and `NEXT_PUBLIC_DEMO_SITE_URL` from `frontend/.env.local` or the Vercel project.", ""]
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    stale = []
    for path, text in ((API_MD, api_md()), (CONFIG_MD, config_md())):
        current = path.read_text(encoding="utf-8").replace("\r\n", "\n") if path.exists() else ""
        if current != text:
            stale.append(path.name)
            if not a.check:
                path.write_text(text, encoding="utf-8", newline="\n")
    if a.check and stale:
        print("out of date:", ", ".join(stale), "- run: python backend/scripts/gen_docs.py")
        return 1
    print("docs written" if stale else "docs up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
