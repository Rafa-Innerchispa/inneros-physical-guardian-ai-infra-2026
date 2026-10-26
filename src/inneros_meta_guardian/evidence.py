"""SQLite incident state and tamper-evident hash-chained forensic audit entries."""
from __future__ import annotations
import hashlib
import json
import sqlite3
import threading
from pathlib import Path


def canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class Store:
    def __init__(self, path: str = ":memory:") -> None:
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        with self.lock:
            self.db.execute("CREATE TABLE IF NOT EXISTS incidents (id TEXT PRIMARY KEY, data TEXT NOT NULL)")
            self.db.execute("CREATE TABLE IF NOT EXISTS audit (seq INTEGER PRIMARY KEY AUTOINCREMENT, incident_id TEXT NOT NULL, event TEXT NOT NULL, payload TEXT NOT NULL, previous_hash TEXT NOT NULL, entry_hash TEXT NOT NULL)")
            self.db.commit()

    def upsert(self, incident: dict) -> None:
        with self.lock:
            self.db.execute("INSERT INTO incidents (id,data) VALUES (?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data", (incident["id"], canonical(incident)))
            self.db.commit()

    def get(self, incident_id: str) -> dict | None:
        with self.lock:
            row = self.db.execute("SELECT data FROM incidents WHERE id=?", (incident_id,)).fetchone()
            return json.loads(row["data"]) if row else None

    def list_incidents(self) -> list[dict]:
        with self.lock:
            rows = self.db.execute("SELECT data FROM incidents ORDER BY rowid DESC LIMIT 50").fetchall()
            return [json.loads(r["data"]) for r in rows]

    def append(self, incident_id: str, event: str, payload: dict) -> dict:
        with self.lock:
            last = self.db.execute("SELECT entry_hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
            prev = last["entry_hash"] if last else "GENESIS"
            p = canonical(payload)
            digest = hashlib.sha256(f"{prev}|{incident_id}|{event}|{p}".encode("utf-8")).hexdigest()
            cursor = self.db.execute("INSERT INTO audit(incident_id,event,payload,previous_hash,entry_hash) VALUES(?,?,?,?,?)", (incident_id, event, p, prev, digest))
            self.db.commit()
            return {"seq": cursor.lastrowid, "incident_id": incident_id, "event": event, "payload": payload, "previous_hash": prev, "entry_hash": digest}

    def audit(self, incident_id: str | None = None) -> list[dict]:
        with self.lock:
            if incident_id:
                rows = self.db.execute("SELECT * FROM audit WHERE incident_id=? ORDER BY seq", (incident_id,)).fetchall()
            else:
                rows = self.db.execute("SELECT * FROM audit ORDER BY seq").fetchall()
            return [{**dict(r), "payload": json.loads(r["payload"])} for r in rows]

    def verify(self) -> dict:
        # Hash chaining spans all incidents; a filtered audit alone cannot prove completeness.
        history = self.audit()
        previous = "GENESIS"
        for row in history:
            expected = hashlib.sha256(f"{previous}|{row['incident_id']}|{row['event']}|{canonical(row['payload'])}".encode("utf-8")).hexdigest()
            if row["previous_hash"] != previous or row["entry_hash"] != expected:
                return {"valid": False, "broken_at": row["seq"], "entries": len(history)}
            previous = row["entry_hash"]
        return {"valid": True, "entries": len(history), "head": previous, "scope": "DEMO_HASH_CHAIN_NOT_PRODUCTION_ATTESTATION"}
