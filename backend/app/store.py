"""SQLite persistence (stdlib sqlite3). Tables: patients, items, flags, reviews, cache, bp_readings."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from .models import Flag, MedicineItem, MedicineItemIn, Patient, PatientIn, ReviewIn, StoredFlag

DEFAULT_DB = Path(__file__).resolve().parent.parent / "oushodh.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS patients (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, name_bn TEXT, age INTEGER NOT NULL,
  district TEXT, conditions TEXT NOT NULL DEFAULT '[]', is_demo INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL, last_checked_at TEXT
);
CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES patients(id),
  brand TEXT NOT NULL, strength TEXT, form TEXT, expiry TEXT, prescriber TEXT, source TEXT,
  confidence REAL NOT NULL DEFAULT 1, schedule TEXT NOT NULL DEFAULT '[]',
  pills_left INTEGER, doses_per_day REAL,
  generic TEXT, drug_class TEXT, match_method TEXT NOT NULL DEFAULT 'not_found',
  match_score REAL, match_source TEXT, prompt_version TEXT, model_id TEXT,
  confirmed INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS flags (
  id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES patients(id),
  key TEXT NOT NULL, code TEXT NOT NULL, severity TEXT NOT NULL, item_ids TEXT NOT NULL,
  evidence TEXT NOT NULL, routed_to TEXT NOT NULL, data_source TEXT NOT NULL,
  meta TEXT NOT NULL DEFAULT '{}', status TEXT NOT NULL DEFAULT 'pending_review',
  active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL,
  reviewer TEXT, note TEXT, reviewed_at TEXT, explanation_bn TEXT,
  UNIQUE (patient_id, key)
);
CREATE TABLE IF NOT EXISTS reviews (
  id INTEGER PRIMARY KEY, flag_id INTEGER NOT NULL REFERENCES flags(id),
  status TEXT NOT NULL, reviewer TEXT NOT NULL, note TEXT, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cache (
  key TEXT PRIMARY KEY, value TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS bp_readings (
  id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES patients(id),
  taken_on TEXT NOT NULL, systolic INTEGER NOT NULL, diastolic INTEGER NOT NULL
);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, path: str | Path | None = None):
        self.path = str(path or os.getenv("OUSHODH_DB") or DEFAULT_DB)
        self._lock = threading.RLock()
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(SCHEMA)

    def _exec(self, sql: str, args: tuple = ()) -> sqlite3.Cursor:
        with self._lock:
            cur = self.db.execute(sql, args)
            self.db.commit()
            return cur

    def _all(self, sql: str, args: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self.db.execute(sql, args).fetchall()

    # ---- patients -------------------------------------------------------
    def _patient(self, r: sqlite3.Row) -> Patient:
        return Patient(
            id=r["id"], name=r["name"], name_bn=r["name_bn"], age=r["age"], district=r["district"],
            conditions=json.loads(r["conditions"]), is_demo=bool(r["is_demo"]),
            created_at=r["created_at"], last_checked_at=r["last_checked_at"],
        )

    def create_patient(self, p: PatientIn) -> Patient:
        cur = self._exec(
            "INSERT INTO patients (name, name_bn, age, district, conditions, is_demo, created_at) VALUES (?,?,?,?,?,?,?)",
            (p.name, p.name_bn, p.age, p.district, json.dumps(p.conditions), int(p.is_demo), now()),
        )
        return self.get_patient(cur.lastrowid)  # type: ignore[return-value]

    def get_patient(self, pid: int) -> Patient | None:
        rows = self._all("SELECT * FROM patients WHERE id = ?", (pid,))
        return self._patient(rows[0]) if rows else None

    def list_patients(self) -> list[Patient]:
        return [self._patient(r) for r in self._all("SELECT * FROM patients ORDER BY id")]

    def mark_checked(self, pid: int) -> None:
        self._exec("UPDATE patients SET last_checked_at = ? WHERE id = ?", (now(), pid))

    # ---- items ----------------------------------------------------------
    def _item(self, r: sqlite3.Row) -> MedicineItem:
        d = dict(r)
        d["schedule"] = json.loads(d["schedule"])
        d["confirmed"] = bool(d["confirmed"])
        d.pop("created_at")
        return MedicineItem(**d)

    def add_item(self, pid: int, item: MedicineItemIn, **match) -> MedicineItem:
        """`match` holds generic, drug_class, match_method, match_score, match_source,
        prompt_version, model_id, confirmed."""
        cols = dict(item.model_dump(), **match)
        cols["schedule"] = json.dumps(cols.get("schedule") or [])
        cols["confirmed"] = int(bool(cols.get("confirmed", False)))
        cols["patient_id"] = pid
        cols["created_at"] = now()
        names = ", ".join(cols)
        marks = ", ".join("?" for _ in cols)
        cur = self._exec(f"INSERT INTO items ({names}) VALUES ({marks})", tuple(cols.values()))
        return self.get_item(cur.lastrowid)  # type: ignore[return-value]

    def get_item(self, item_id: int) -> MedicineItem | None:
        rows = self._all("SELECT * FROM items WHERE id = ?", (item_id,))
        return self._item(rows[0]) if rows else None

    def list_items(self, pid: int, confirmed_only: bool = False) -> list[MedicineItem]:
        sql = "SELECT * FROM items WHERE patient_id = ?" + (" AND confirmed = 1" if confirmed_only else "")
        return [self._item(r) for r in self._all(sql + " ORDER BY id", (pid,))]

    def update_item(self, item_id: int, **fields) -> MedicineItem | None:
        if not fields:
            return self.get_item(item_id)
        if "schedule" in fields:
            fields["schedule"] = json.dumps(fields["schedule"])
        if "confirmed" in fields:
            fields["confirmed"] = int(bool(fields["confirmed"]))
        sets = ", ".join(f"{k} = ?" for k in fields)
        self._exec(f"UPDATE items SET {sets} WHERE id = ?", (*fields.values(), item_id))
        return self.get_item(item_id)

    def clear_items(self, pid: int) -> None:
        self._exec("DELETE FROM items WHERE patient_id = ?", (pid,))

    def delete_item(self, item_id: int) -> bool:
        return self._exec("DELETE FROM items WHERE id = ?", (item_id,)).rowcount > 0

    # ---- flags ----------------------------------------------------------
    def _flag(self, r: sqlite3.Row) -> StoredFlag:
        d = dict(r)
        d["item_ids"] = json.loads(d["item_ids"])
        d["meta"] = json.loads(d["meta"])
        d["active"] = bool(d["active"])
        return StoredFlag(**d)

    def sync_flags(self, pid: int, flags: list[Flag]) -> list[StoredFlag]:
        """Upsert flags by key. A flag that already exists keeps its review decision;
        a flag the rules no longer produce is marked inactive (resolved), not deleted."""
        keys = [f.key for f in flags]
        with self._lock:
            for f in flags:
                self.db.execute(
                    """INSERT INTO flags (patient_id, key, code, severity, item_ids, evidence, routed_to,
                                          data_source, meta, created_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?)
                       ON CONFLICT (patient_id, key) DO UPDATE SET
                         item_ids = excluded.item_ids, evidence = excluded.evidence,
                         meta = excluded.meta, active = 1""",
                    (pid, f.key, f.code, f.severity, json.dumps(f.item_ids), f.evidence, f.routed_to,
                     f.data_source, json.dumps(f.meta), now()),
                )
            marks = ", ".join("?" for _ in keys) or "''"
            self.db.execute(
                f"UPDATE flags SET active = 0 WHERE patient_id = ? AND key NOT IN ({marks})", (pid, *keys)
            )
            self.db.commit()
        return self.list_flags(pid)

    def list_flags(self, pid: int | None = None, statuses: tuple[str, ...] | None = None,
                   active_only: bool = True) -> list[StoredFlag]:
        sql, args = "SELECT * FROM flags WHERE 1=1", []
        if pid is not None:
            sql += " AND patient_id = ?"
            args.append(pid)
        if statuses:
            sql += f" AND status IN ({', '.join('?' for _ in statuses)})"
            args += list(statuses)
        if active_only:
            sql += " AND active = 1"
        sql += " ORDER BY CASE severity WHEN 'red' THEN 0 ELSE 1 END, created_at, id"
        return [self._flag(r) for r in self._all(sql, tuple(args))]

    def get_flag(self, flag_id: int) -> StoredFlag | None:
        rows = self._all("SELECT * FROM flags WHERE id = ?", (flag_id,))
        return self._flag(rows[0]) if rows else None

    def review_flag(self, flag_id: int, review: ReviewIn, explanation_bn: str | None) -> StoredFlag:
        ts = now()
        with self._lock:
            self.db.execute(
                "UPDATE flags SET status = ?, reviewer = ?, note = ?, reviewed_at = ?, explanation_bn = ? WHERE id = ?",
                (review.status, review.reviewer, review.note, ts, explanation_bn, flag_id),
            )
            self.db.execute(
                "INSERT INTO reviews (flag_id, status, reviewer, note, created_at) VALUES (?,?,?,?,?)",
                (flag_id, review.status, review.reviewer, review.note, ts),
            )
            self.db.commit()
        return self.get_flag(flag_id)  # type: ignore[return-value]

    def undo_review(self, flag_id: int, reviewer: str) -> StoredFlag:
        ts = now()
        with self._lock:
            self.db.execute(
                "UPDATE flags SET status = 'pending_review', reviewer = NULL, note = NULL, reviewed_at = NULL, "
                "explanation_bn = NULL WHERE id = ?", (flag_id,),
            )
            self.db.execute(
                "INSERT INTO reviews (flag_id, status, reviewer, note, created_at) VALUES (?,?,?,?,?)",
                (flag_id, "undone", reviewer, None, ts),
            )
            self.db.commit()
        return self.get_flag(flag_id)  # type: ignore[return-value]

    def list_reviews(self, pid: int) -> list[dict]:
        rows = self._all(
            """SELECT r.*, f.code, f.severity, f.evidence FROM reviews r JOIN flags f ON f.id = r.flag_id
               WHERE f.patient_id = ? ORDER BY r.created_at DESC, r.id DESC""", (pid,),
        )
        return [dict(r) for r in rows]

    # ---- BP readings ----------------------------------------------------
    def add_bp(self, pid: int, taken_on: str, systolic: int, diastolic: int) -> None:
        self._exec("INSERT INTO bp_readings (patient_id, taken_on, systolic, diastolic) VALUES (?,?,?,?)",
                   (pid, taken_on, systolic, diastolic))

    def list_bp(self, pid: int, limit: int = 7) -> list[dict]:
        rows = self._all(
            "SELECT taken_on, systolic, diastolic FROM bp_readings WHERE patient_id = ? ORDER BY taken_on DESC LIMIT ?",
            (pid, limit),
        )
        return [dict(r) for r in reversed(rows)]

    # ---- cache ----------------------------------------------------------
    def cache_get(self, key: str) -> str | None:
        rows = self._all("SELECT value FROM cache WHERE key = ?", (key,))
        return rows[0]["value"] if rows else None

    def cache_set(self, key: str, value: str) -> None:
        self._exec("INSERT OR REPLACE INTO cache (key, value, created_at) VALUES (?,?,?)", (key, value, now()))
