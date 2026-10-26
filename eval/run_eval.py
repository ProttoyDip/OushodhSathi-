"""Extraction eval: run the shelf agent on labelled photos and report accuracy.

  backend/.venv/Scripts/python eval/run_eval.py          (Windows)
  backend/.venv/bin/python eval/run_eval.py              (macOS/Linux)

Reads eval/labels.csv (image_path,brand,strength; one row per medicine visible in a
photo, image_path relative to eval/). Writes eval/results_<prompt_version>.json.
Needs a vision provider configured in backend/.env. Never prints keys.
"""
from __future__ import annotations

import asyncio
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "backend"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT.parent / "backend" / ".env")

from app import prompts  # noqa: E402
from app.agent import read_shelf  # noqa: E402
from app.brands import normalise  # noqa: E402
from app.llm_router import NoProviderAvailable  # noqa: E402


def norm_strength(s: str | None) -> str:
    return re.sub(r"\s+", "", (s or "").lower())


async def main() -> int:
    labels: dict[str, list[dict]] = defaultdict(list)
    with (ROOT / "labels.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            labels[r["image_path"]].append(r)
    if not labels:
        print("eval/labels.csv has no rows yet. See eval/README.md.")
        return 1

    per_image, brand_hits, strength_hits, total, confidences = [], 0, 0, 0, []
    model_id = None
    for image_path, expected in labels.items():
        photo = (ROOT / image_path).read_bytes()
        try:
            outcome = await read_shelf([photo])
        except NoProviderAvailable as e:
            print(f"No vision provider available: {e}")
            return 2
        model_id = model_id or outcome.model_id
        got = [s.item for s in outcome.items]
        confidences += [g.confidence for g in got]
        rows = []
        for exp in expected:
            total += 1
            match = next((g for g in got if normalise(g.brand) == normalise(exp["brand"])), None)
            b_ok = match is not None
            s_ok = b_ok and norm_strength(match.strength) == norm_strength(exp["strength"])
            brand_hits += b_ok
            strength_hits += s_ok
            rows.append({"expected": exp, "brand_ok": b_ok, "strength_ok": s_ok,
                         "got": match.model_dump() if match else None})
        per_image.append({"image": image_path, "results": rows,
                          "extra_items": [g.brand for g in got
                                          if normalise(g.brand) not in {normalise(e["brand"]) for e in expected}]})
        print(f"{image_path}: {sum(r['brand_ok'] for r in rows)}/{len(rows)} brands")

    version = prompts.version("extract_strip")
    summary = {
        "prompt_version": version,
        "model_id": model_id,
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "images": len(labels),
        "labelled_items": total,
        "brand_accuracy": round(brand_hits / total, 3),
        "strength_accuracy": round(strength_hits / total, 3),
        "avg_confidence": round(sum(confidences) / len(confidences), 3) if confidences else None,
        "per_image": per_image,
    }
    out = ROOT / f"results_{version}.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nbrand accuracy    {summary['brand_accuracy']:.1%}  ({brand_hits}/{total})")
    print(f"strength accuracy {summary['strength_accuracy']:.1%}  ({strength_hits}/{total})")
    print(f"avg confidence    {summary['avg_confidence']}")
    print(f"model             {model_id}\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
