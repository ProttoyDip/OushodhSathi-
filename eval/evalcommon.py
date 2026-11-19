"""Shared command-line handling for the strip and BP evals: --labels, --out, --kind.

Real and synthetic results never mix (Prompt 14, rule 1):
- image_path in a label file is resolved against that file's own folder, so eval/synthetic/labels.csv
  finds eval/synthetic/photos/...;
- a synthetic run may not write to a real results file (eval/results_*.json, eval/bp_results_*.json),
  and by default writes next to its own labels;
- the real-photo minimum (MIN_PHOTOS) applies to real runs only.
"""
from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path

EVAL = Path(__file__).resolve().parent
_YM = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
CONDITIONS = {"clear", "cut_strip", "glare", "bangla", "handwritten"}


class LabelError(ValueError):
    """A label file problem, with every bad row listed so it can be fixed in one go."""


@dataclass
class Options:
    labels: Path
    out: Path
    kind: str           # real | synthetic
    per_provider: bool

    @property
    def base(self) -> Path:
        """Folder that image_path values are relative to."""
        return self.labels.parent


def is_real_results_path(path: Path) -> bool:
    p = path.resolve()
    return p.parent == EVAL and re.fullmatch(r"(bp_)?results_.*\.json", p.name) is not None


def parse(argv: list[str] | None, *, default_labels: str, out_name: str, per_provider: bool = True) -> Options:
    """out_name: the results file name for the current prompt version, e.g. results_extract_strip.v1.json."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", type=Path, default=EVAL / default_labels, help="label CSV")
    ap.add_argument("--out", type=Path, help="results JSON (default: next to the labels for synthetic runs)")
    ap.add_argument("--kind", choices=["real", "synthetic"], default="real")
    if per_provider:
        ap.add_argument("--per-provider", action="store_true")
    a = ap.parse_args(argv)
    labels = a.labels if a.labels.is_absolute() else (Path.cwd() / a.labels)
    labels = labels.resolve()
    if a.out is not None:
        out = (a.out if a.out.is_absolute() else Path.cwd() / a.out).resolve()
    else:
        out = (EVAL if a.kind == "real" else labels.parent) / out_name
    if a.kind == "synthetic" and is_real_results_path(out):
        raise SystemExit(f"Refusing to write synthetic results to {out}: that is a real-photo results file. "
                         f"Use --out inside eval/synthetic/ (or leave --out out).")
    if a.kind == "real" and labels.parent != EVAL:
        raise SystemExit(f"--kind real expects labels in {EVAL} (got {labels}); synthetic sets need --kind synthetic.")
    return Options(labels, out, a.kind, bool(getattr(a, "per_provider", False)))


def read_rows(path: Path, required: tuple[str, ...]) -> list[dict]:
    """Rows of a label CSV; LabelError listing every problem if the header or rows are wrong."""
    if not path.exists():
        raise LabelError(f"{path}: file not found")
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        missing = [c for c in required if c not in header]
        if missing:
            raise LabelError(f"{path.name}: missing column(s) {', '.join(missing)} (header is {', '.join(header) or 'empty'})")
        return [r for r in reader if any((v or "").strip() for v in r.values())]


def check_strip_rows(rows: list[dict], base: Path) -> None:
    problems = []
    for i, r in enumerate(rows, 2):  # line 1 is the header
        if not (r.get("image_path") or "").strip():
            problems.append(f"line {i}: image_path is empty")
        elif not (base / r["image_path"]).exists():
            problems.append(f"line {i}: image not found: {r['image_path']}")
        if not (r.get("brand") or "").strip():
            problems.append(f"line {i}: brand is empty")
        exp = (r.get("expiry") or "").strip()
        if exp and not _YM.match(exp):
            problems.append(f"line {i}: expiry {exp!r} is not YYYY-MM (leave it empty if not visible)")
        cond = (r.get("condition") or "").strip()
        if cond and cond not in CONDITIONS:
            problems.append(f"line {i}: condition {cond!r} is not one of {', '.join(sorted(CONDITIONS))}")
    if problems:
        raise LabelError("label file problems:\n  " + "\n  ".join(problems))


def check_bp_rows(rows: list[dict], base: Path) -> None:
    problems = []
    for i, r in enumerate(rows, 2):
        if not (base / (r.get("image_path") or "")).is_file():
            problems.append(f"line {i}: image not found: {r.get('image_path')!r}")
        for k in ("systolic", "diastolic", "pulse"):
            v = (r.get(k) or "").strip()
            if k != "pulse" and not v:
                problems.append(f"line {i}: {k} is empty")
            elif v and not v.isdigit():
                problems.append(f"line {i}: {k} {v!r} is not a whole number")
    if problems:
        raise LabelError("label file problems:\n  " + "\n  ".join(problems))


def provenance(opts: Options, n_photos: int) -> dict:
    """Fields every results JSON carries, so a reader always knows what kind of number it is."""
    try:
        labels_file = str(opts.labels.relative_to(EVAL.parent)).replace("\\", "/")
    except ValueError:
        labels_file = str(opts.labels)
    out = {"kind": opts.kind, "labels_file": labels_file, "n_photos": n_photos}
    if opts.kind == "synthetic":
        out["label"] = {"en": "Synthetic benchmark (computer-drawn images) — not real-photo accuracy",
                        "bn": "কৃত্রিম বেঞ্চমার্ক (কম্পিউটারে আঁকা ছবি) — আসল ছবিতে নির্ভুলতা নয়"}
    return out
