"""Label eval photos in the browser: one photo at a time, type what is printed, save to eval/labels.csv.

  backend/.venv/Scripts/python backend/scripts/label_photos.py     (Windows)
  backend/.venv/bin/python backend/scripts/label_photos.py         (macOS / Linux)

Opens http://127.0.0.1:8765 (local only, nothing leaves the machine). It shows each photo in eval/photos/
that has no label yet, with rows for every medicine visible: brand, strength and expiry as printed, and
the photo's condition. Saving requires ticking the privacy checklist (no faces, names, phone numbers or
addresses in the photo). A photo you mark "skip" is not labelled and stays out of the eval.
"""
from __future__ import annotations

import csv
import html
import mimetypes
import re
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

EVAL = Path(__file__).resolve().parents[2] / "eval"
PHOTOS = EVAL / "photos"
LABELS = EVAL / "labels.csv"
FIELDS = ["image_path", "brand", "strength", "expiry", "condition"]
CONDITIONS = ["clear", "cut_strip", "glare", "bangla", "handwritten"]
ROWS = 6
_YM = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
PORT = 8765


def labelled() -> set[str]:
    if not LABELS.exists():
        return set()
    with LABELS.open(encoding="utf-8") as f:
        return {r["image_path"] for r in csv.DictReader(f)}


def todo() -> list[str]:
    done = labelled()
    exts = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
    return [f"photos/{p.name}" for p in sorted(PHOTOS.glob("*")) if p.suffix.lower() in exts
            and f"photos/{p.name}" not in done]


def append(rows: list[dict]) -> None:
    """Writes the header (with the newer columns) if needed; older 3-column files are upgraded."""
    existing = []
    if LABELS.exists():
        with LABELS.open(encoding="utf-8") as f:
            existing = list(csv.DictReader(f))
    with LABELS.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in existing + rows:
            w.writerow({k: r.get(k, "") or "" for k in FIELDS})


def validate(form: dict[str, list[str]], image: str) -> tuple[list[dict], list[str]]:
    errors, rows = [], []
    if not form.get("private"):
        errors.append("Tick the privacy checklist first.")
    cond = (form.get("condition") or ["clear"])[0]
    if cond not in CONDITIONS:
        errors.append("Pick a condition.")
    for i in range(ROWS):
        brand = (form.get(f"brand{i}") or [""])[0].strip()
        if not brand:
            continue
        expiry = (form.get(f"expiry{i}") or [""])[0].strip()
        if expiry and not _YM.match(expiry):
            errors.append(f"Row {i + 1}: expiry must be YYYY-MM, or empty if it is not visible.")
        rows.append({"image_path": image, "brand": brand[:80],
                     "strength": (form.get(f"strength{i}") or [""])[0].strip()[:40], "expiry": expiry, "condition": cond})
    if not rows:
        errors.append("Type at least one brand, or press Skip.")
    return rows, errors


PAGE = """<!doctype html><meta charset="utf-8"><title>Label eval photos</title>
<style>body{{font:16px system-ui;margin:16px;max-width:1100px}} .wrap{{display:grid;grid-template-columns:1fr 420px;gap:20px}}
img{{max-width:100%;max-height:85vh;border:1px solid #ccc}} input,select{{font:inherit;padding:6px;width:100%;box-sizing:border-box}}
table{{width:100%}} td{{padding:2px}} .err{{color:#b00020}} button{{font:inherit;padding:10px 16px;margin-top:8px}}
@media (max-width:800px){{.wrap{{grid-template-columns:1fr}}}}</style>
<h1>Label eval photos <small>({left} left)</small></h1>{body}"""


def page(image: str | None, left: int, errors: list[str] | None = None) -> str:
    if image is None:
        return PAGE.format(left=0, body="<p>Every photo in eval/photos/ is labelled. Run eval/run_eval.py next.</p>")
    rows = "".join(f"<tr><td><input name=brand{i} placeholder='Brand as printed'></td>"
                   f"<td><input name=strength{i} placeholder='500 mg'></td>"
                   f"<td><input name=expiry{i} placeholder='2027-03'></td></tr>" for i in range(ROWS))
    conds = "".join(f"<option>{c}</option>" for c in CONDITIONS)
    errs = "".join(f"<p class=err>{html.escape(e)}</p>" for e in errors or [])
    body = f"""<div class=wrap><img src="/img/{quote(image)}" alt="photo to label">
<form method=post action="/save"><input type=hidden name=image value="{html.escape(image)}">
<p><b>{html.escape(image)}</b></p>{errs}
<label><input type=checkbox name=private value=1 style="width:auto"> No faces, names, phone numbers or addresses
are visible (cover or crop them first).</label>
<p>Condition <select name=condition>{conds}</select></p>
<table><tr><th>Brand</th><th>Strength</th><th>Expiry</th></tr>{rows}</table>
<p>One row per medicine visible. Type exactly what is printed; leave expiry empty if it is cut off.</p>
<button>Save and next</button> <button formaction="/skip">Skip this photo</button></form></div>"""
    return PAGE.format(left=left, body=body)


class Handler(BaseHTTPRequestHandler):
    skipped: set[str] = set()

    def _send(self, code: int, body: bytes, ctype: str = "text/html; charset=utf-8") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _next(self, errors: list[str] | None = None, image: str | None = None) -> None:
        left = [p for p in todo() if p not in self.skipped]
        self._send(200, page(image or (left[0] if left else None), len(left), errors).encode())

    def do_GET(self) -> None:  # noqa: N802
        path = unquote(urlparse(self.path).path)
        if path.startswith("/img/photos/"):
            f = (PHOTOS / Path(path).name).resolve()
            if f.parent != PHOTOS.resolve() or not f.exists():
                return self._send(404, b"not found", "text/plain")
            return self._send(200, f.read_bytes(), mimetypes.guess_type(f.name)[0] or "application/octet-stream")
        self._next()

    def do_POST(self) -> None:  # noqa: N802
        form = parse_qs(self.rfile.read(int(self.headers.get("Content-Length", 0))).decode())
        image = (form.get("image") or [""])[0]
        if image not in todo():
            return self._next()
        if self.path == "/skip":
            self.skipped.add(image)
            return self._next()
        rows, errors = validate(form, image)
        if errors:
            return self._next(errors, image)
        append(rows)
        self._next()

    def log_message(self, *args) -> None:  # quiet
        pass


def main() -> None:
    PHOTOS.mkdir(parents=True, exist_ok=True)
    print(f"{len(todo())} photos to label in {PHOTOS}\nOpen http://127.0.0.1:{PORT}  (Ctrl+C to stop)")
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    webbrowser.open(f"http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
