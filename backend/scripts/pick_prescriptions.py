"""Pick and label real handwritten prescriptions from the Mendeley dataset, locally (nothing is uploaded).

  backend/.venv/Scripts/python backend/scripts/pick_prescriptions.py     (Windows)
  backend/.venv/bin/python backend/scripts/pick_prescriptions.py         (macOS / Linux)

Dataset: Badhon D.R. et al., "Image-to-Text Bilingual Dataset from Medical Prescriptions", Mendeley Data,
V2, 2026, doi:10.17632/tg2hm7n2bs.2, licence CC BY 4.0. Unzip it into eval/raw/prescriptions_bd/ (git-ignored;
the dataset is never committed). Expects Prescriptions_Dataset.csv and an images/ folder.

Opens http://127.0.0.1:8766. Step 1 lists the 20 prescriptions whose transcription names the most brands from
backend/data/brands_seed.csv / brands_bn.csv; tick up to 10. Step 2, for each one: confirm the brand(s) and
strength(s) as written (expiry stays empty, condition "handwritten"), black out every patient name, doctor
name, phone, address, registration number or QR code by dragging rectangles, and tick the privacy check.
Without the tick nothing is saved. Only the redacted copy is written, to eval/photos/rx_mendeley_XX.jpg
(neutral names, no metadata), and its rows are appended to eval/labels.csv with source=mendeley:tg2hm7n2bs.
"""
from __future__ import annotations

import csv
import html
import io
import json
import re
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.brands import normalise, normalise_bn  # noqa: E402

RAW = ROOT / "eval" / "raw" / "prescriptions_bd"
PHOTOS = ROOT / "eval" / "photos"
LABELS = ROOT / "eval" / "labels.csv"
SOURCE = "mendeley:tg2hm7n2bs"
TOP, MAX_PICK, PORT = 20, 10, 8766
ROWS = 6


# ---- pure helpers (tested) ------------------------------------------------------------------------

def load_texts(csv_path: Path) -> dict[str, str]:
    """image file name -> its transcription. The dataset CSV continues one prescription over several
    physical rows; rows without a file name belong to the image above them."""
    texts: dict[str, str] = {}
    cur = None
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            name = (row[0] if row else "").strip()
            if name:
                cur = name
                texts[cur] = " ".join(c for c in row[1:] if c.strip())
            elif cur is not None:
                texts[cur] = (texts[cur] + " " + " ".join(c for c in row if c.strip())).strip()
    return texts


def brand_tables() -> tuple[list[str], list[tuple[str, str]]]:
    data = ROOT / "backend" / "data"
    seed = [r["brand"] for r in csv.DictReader((data / "brands_seed.csv").open(encoding="utf-8")) if r.get("brand")]
    bn = [(r["bn"], r["brand"]) for r in csv.DictReader((data / "brands_bn.csv").open(encoding="utf-8"))
          if r.get("bn") and r.get("brand")]
    return seed, bn


def find_brands(text: str, seed: list[str], bn: list[tuple[str, str]]) -> list[str]:
    """Table brands named in a transcription: whole-word on the normalised Latin text, substring on the
    normalised Bangla text. Returned in table order, longest first so "Amdocal Plus" beats "Amdocal"."""
    low = " ".join(normalise(text).split())
    found = []
    for b in sorted(seed, key=len, reverse=True):
        nb = normalise(b)
        if nb and re.search(r"(?<![a-z0-9])" + re.escape(nb) + r"(?![a-z0-9])", low):
            found.append(b)
    bn_text = normalise_bn(text)
    for alias, brand in bn:
        a = normalise_bn(alias)
        if a and a in bn_text and brand not in found:
            found.append(brand)
    # drop a brand that is only part of a longer one found ("Amdocal" inside "Amdocal Plus")
    return [b for b in found if not any(o != b and normalise(b) in normalise(o).split() and normalise(o).startswith(normalise(b))
                                        for o in found)]


def candidates(texts: dict[str, str], seed, bn, k: int = TOP) -> list[tuple[str, list[str]]]:
    """k prescriptions that name table brands, chosen for coverage: each pick is the one adding the most
    brands not yet shown (ties: more brands, then file name), so 20 copies of the same printed list
    never crowd out the rest."""
    pool = sorted(((n, find_brands(t, seed, bn)) for n, t in texts.items()), key=lambda x: x[0])
    pool = [(n, b) for n, b in pool if b]
    picked, seen = [], set()
    while pool and len(picked) < k:
        best = max(pool, key=lambda x: (len(set(x[1]) - seen), len(x[1]), [-ord(c) for c in x[0]]))
        picked.append(best)
        seen |= set(best[1])
        pool.remove(best)
    return picked


def next_names(photos: Path, n: int) -> list[str]:
    taken = {int(m.group(1)) for p in photos.glob("rx_mendeley_*.jpg") if (m := re.match(r"rx_mendeley_(\d+)\.jpg", p.name))}
    out, i = [], 1
    while len(out) < n:
        if i not in taken:
            out.append(f"rx_mendeley_{i:02d}.jpg")
        i += 1
    return out


def redact(image: bytes, rects: list[list[float]]) -> bytes:
    """Black out rectangles given as [x0, y0, x1, y1] fractions of the width and height. The copy is
    re-encoded without any metadata (no EXIF)."""
    from PIL import Image, ImageDraw, ImageOps

    img = ImageOps.exif_transpose(Image.open(io.BytesIO(image))).convert("RGB")
    w, h = img.size
    d = ImageDraw.Draw(img)
    for r in rects:
        x0, y0, x1, y1 = (max(0.0, min(1.0, float(v))) for v in r)
        d.rectangle([min(x0, x1) * w, min(y0, y1) * h, max(x0, x1) * w, max(y0, y1) * h], fill="black")
    out = io.BytesIO()
    img.save(out, "JPEG", quality=90)
    return out.getvalue()


def validate(form: dict[str, list[str]]) -> tuple[list[dict], list[list[float]], list[str]]:
    """-> (label rows without image_path, rectangles, errors). The privacy tick is required."""
    errors = []
    if not form.get("private"):
        errors.append("Tick the privacy check first: no patient name, doctor name, phone, address, "
                      "registration number or QR code may be visible (black them out).")
    rows = []
    for i in range(ROWS):
        brand = (form.get(f"brand{i}") or [""])[0].strip()
        if brand:
            rows.append({"brand": brand[:80], "strength": (form.get(f"strength{i}") or [""])[0].strip()[:40],
                         "expiry": "", "condition": "handwritten", "source": SOURCE})
    if not rows:
        errors.append("Confirm at least one brand that is written on the prescription.")
    try:
        rects = json.loads((form.get("rects") or ["[]"])[0])
        assert isinstance(rects, list) and all(isinstance(r, list) and len(r) == 4 for r in rects)
    except (ValueError, AssertionError):
        rects, errors = [], [*errors, "The blacked-out areas could not be read; draw them again."]
    return rows, rects, errors


def save(image_name: str, image: bytes, rows: list[dict], rects: list[list[float]],
         photos: Path = PHOTOS, labels: Path = LABELS) -> str:
    import label_photos

    photos.mkdir(parents=True, exist_ok=True)
    out = next_names(photos, 1)[0]
    (photos / out).write_bytes(redact(image, rects))
    label_photos.LABELS = labels
    label_photos.append([{**r, "image_path": f"photos/{out}"} for r in rows])
    return out


# ---- the local page -------------------------------------------------------------------------------

STYLE = """<style>body{font:16px system-ui;margin:16px;max-width:1200px} .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}
.card{border:1px solid #ccc;border-radius:10px;padding:10px} .card img{width:100%;max-height:260px;object-fit:contain;background:#f4f4f4}
.t{font-size:13px;color:#444;max-height:90px;overflow:auto;white-space:pre-wrap} .b{font-weight:600;color:#2a3b91}
.wrap{display:grid;grid-template-columns:1fr 420px;gap:20px} canvas{max-width:100%;border:1px solid #ccc;cursor:crosshair}
input{font:inherit;padding:6px;width:100%;box-sizing:border-box} .err{color:#b00020} button{font:inherit;padding:10px 16px}
@media(max-width:800px){.wrap{grid-template-columns:1fr}}</style>"""


class State:
    texts: dict[str, str] = {}
    cands: list[tuple[str, list[str]]] = []
    queue: list[str] = []


def image_index(root: Path = RAW) -> dict[str, Path]:
    """Annotation file name -> the image on disk, matched by stem (the dataset mixes .jpg and .jpeg, and
    its image folder is itself named "... images.jpg")."""
    out = {}
    for f in root.rglob("*"):
        if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png"):
            out.setdefault(f.stem, f)
    return out


IMAGES: dict[str, Path] = {}


def _image(name: str) -> Path | None:
    return IMAGES.get(Path(name).stem)


def page_pick() -> str:
    cards = "".join(
        f"<label class=card><input type=checkbox name=pick value='{html.escape(n)}' style='width:auto'> <b>{html.escape(n)}</b>"
        f"<img src='/img/{quote(n)}' alt=''><div class=b>{html.escape(', '.join(b))}</div>"
        f"<div class=t>{html.escape(State.texts[n][:600])}</div></label>" for n, b in State.cands)
    return (f"<!doctype html><meta charset=utf-8><title>Pick prescriptions</title>{STYLE}<h1>Pick up to {MAX_PICK} prescriptions</h1>"
            f"<p>{len(State.cands)} candidates whose transcription names a brand from our tables (most brands first).</p>"
            f"<form method=post action=/pick><div class=grid>{cards}</div><p><button>Continue with the ticked ones</button></p></form>")


def page_label(name: str, errors: list[str] | None = None) -> str:
    found = dict(State.cands).get(name, [])
    rows = "".join(f"<tr><td><input name=brand{i} value='{html.escape(found[i] if i < len(found) else '')}'></td>"
                   f"<td><input name=strength{i} placeholder='as written, e.g. 500 mg'></td></tr>" for i in range(ROWS))
    errs = "".join(f"<p class=err>{html.escape(e)}</p>" for e in errors or [])
    return f"""<!doctype html><meta charset=utf-8><title>Label {html.escape(name)}</title>{STYLE}
<h1>{html.escape(name)} <small>({len(State.queue)} left)</small></h1>{errs}
<div class=wrap><div><canvas id=c></canvas><p>Drag to black out a name, phone, address, registration number or QR code.
<button type=button onclick="R=[];draw()">Clear the black boxes</button></p></div>
<form method=post action=/save onsubmit="document.getElementById('rects').value=JSON.stringify(R)">
<input type=hidden name=image value="{html.escape(name)}"><input type=hidden id=rects name=rects value="[]">
<p>Transcription from the dataset (check against the image):</p><div class=t>{html.escape(State.texts.get(name, '')[:1500])}</div>
<table><tr><th>Brand as written</th><th>Strength as written</th></tr>{rows}</table>
<p>Remove a row by clearing its brand. Expiry stays empty; condition is "handwritten".</p>
<label><input type=checkbox name=private value=1 style="width:auto"> No patient name, doctor name, phone, address,
registration number or QR code is visible in the saved copy.</label>
<p><button>Save the redacted copy</button> <button formaction=/skip>Skip</button></p></form></div>
<script>
const img=new Image(), c=document.getElementById('c'), x=c.getContext('2d'); let R=[], s=null;
img.onload=()=>{{c.width=img.naturalWidth;c.height=img.naturalHeight;draw()}}; img.src='/img/{quote(name)}';
function draw(){{x.drawImage(img,0,0);x.fillStyle='#000';for(const r of R)x.fillRect(r[0]*c.width,r[1]*c.height,(r[2]-r[0])*c.width,(r[3]-r[1])*c.height)}}
function pt(e){{const b=c.getBoundingClientRect();return[(e.clientX-b.left)/b.width,(e.clientY-b.top)/b.height]}}
c.onmousedown=e=>{{s=pt(e)}}; c.onmouseup=e=>{{if(!s)return;const p=pt(e);
R.push([Math.min(s[0],p[0]),Math.min(s[1],p[1]),Math.max(s[0],p[0]),Math.max(s[1],p[1])]);s=null;draw()}};
</script>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str = "text/html; charset=utf-8") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _next(self, errors=None, name=None):
        if name or State.queue:
            return self._send(200, page_label(name or State.queue[0], errors).encode())
        if State.cands and not State.queue:
            return self._send(200, page_pick().encode())

    def do_GET(self):  # noqa: N802
        path = unquote(urlparse(self.path).path)
        if path.startswith("/img/"):
            f = _image(Path(path[5:]).name)
            if f is None:
                return self._send(404, b"not found", "text/plain")
            return self._send(200, f.read_bytes(), "image/jpeg")
        self._send(200, (page_label(State.queue[0]) if State.queue else page_pick()).encode())

    def do_POST(self):  # noqa: N802
        form = parse_qs(self.rfile.read(int(self.headers.get("Content-Length", 0))).decode())
        if self.path == "/pick":
            State.queue = [n for n in form.get("pick", []) if n in dict(State.cands)][:MAX_PICK]
            return self._next()
        name = (form.get("image") or [""])[0]
        if name not in State.queue:
            return self._next()
        if self.path == "/skip":
            State.queue.remove(name)
            return self._next()
        rows, rects, errors = validate(form)
        if errors:
            return self._next(errors, name)
        src = _image(name)
        if src is None:
            return self._next(["The image file for this prescription was not found."], name)
        out = save(name, src.read_bytes(), rows, rects)
        print(f"saved eval/photos/{out} ({len(rows)} row(s))")
        State.queue.remove(name)
        if not State.queue:
            return self._send(200, b"<p>Done. Run eval/run_eval.py next.</p>")
        self._next()

    def log_message(self, *args):  # quiet
        pass


def main() -> None:
    csv_path = RAW / "Prescriptions_Dataset.csv"
    if not csv_path.exists():
        sys.exit(f"Unzip the dataset into {RAW} first (Prescriptions_Dataset.csv and the images).")
    State.texts = load_texts(csv_path)
    IMAGES.update(image_index())
    State.texts = {n: t for n, t in State.texts.items() if _image(n) is not None}
    seed, bn = brand_tables()
    State.cands = candidates(State.texts, seed, bn)
    print(f"{len(State.texts)} prescriptions, {len(State.cands)} shown. Open http://127.0.0.1:{PORT} (Ctrl+C to stop)")
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    webbrowser.open(f"http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
