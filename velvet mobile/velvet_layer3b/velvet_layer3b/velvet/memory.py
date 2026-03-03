from __future__ import annotations
import json, sqlite3, time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

@dataclass(frozen=True)
class MemoryEvent:
    ts: float
    kind: str
    speaker: str
    text: str
    meta: Dict[str, Any]

class VelvetMemory:
    def __init__(self, db_file: Path):
        self.db_file = db_file
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.db_file))
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        return con

    def _init_db(self) -> None:
        con = self._connect()
        try:
            con.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    kind TEXT NOT NULL,
                    speaker TEXT NOT NULL,
                    text TEXT NOT NULL,
                    meta_json TEXT NOT NULL
                );
            """)
            con.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);")
            con.execute("CREATE INDEX IF NOT EXISTS idx_events_kind ON events(kind);")
            con.commit()
        finally:
            con.close()

    def append(self, kind: str, speaker: str, text: str,
               meta: Optional[Dict[str, Any]] = None,
               ts: Optional[float] = None) -> None:
        meta = meta or {}
        ts = ts if ts is not None else time.time()
        con = self._connect()
        try:
            con.execute(
                "INSERT INTO events(ts, kind, speaker, text, meta_json) VALUES (?, ?, ?, ?, ?)",
                (float(ts), kind, speaker, text, json.dumps(meta, ensure_ascii=False, separators=(',', ':'))),
            )
            con.commit()
        finally:
            con.close()

    def tail(self, limit: int = 30, kind: Optional[str] = None) -> List[MemoryEvent]:
        con = self._connect()
        try:
            if kind:
                rows = con.execute(
                    "SELECT ts, kind, speaker, text, meta_json FROM events "
                    "WHERE kind=? ORDER BY id DESC LIMIT ?",
                    (kind, limit),
                ).fetchall()
            else:
                rows = con.execute(
                    "SELECT ts, kind, speaker, text, meta_json FROM events "
                    "ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            out = []
            for ts, k, sp, txt, meta_json in rows:
                try:
                    meta = json.loads(meta_json)
                except Exception:
                    meta = {}
                out.append(MemoryEvent(float(ts), k, sp, txt, meta))
            return list(reversed(out))
        finally:
            con.close()

    def recent_chat_context(self, limit_pairs: int = 6) -> List[Tuple[str, str]]:
        events = self.tail(limit=limit_pairs * 2 + 10, kind="chat")
        ctx: List[Tuple[str, str]] = []
        for e in events:
            if e.speaker in ("user", "velvet"):
                ctx.append((e.speaker, e.text))
        return ctx[-limit_pairs * 2 :]
