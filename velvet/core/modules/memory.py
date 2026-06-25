# SPDX-License-Identifier: GPL-3.0-only
# velvet/core/modules/memory.py
from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from velvet.core.context import get_event_bus, get_registry
from velvet.core.interfaces.memory import MemoryInterface
from velvet.core.schemas.memory import MemoryRecord

log = logging.getLogger("velvet.module.memory")


class _FileMemoryAdapter(MemoryInterface):
    """File-backed adapter for Velvet's append-only memory ledger."""

    def __init__(self, module: "MemoryModule") -> None:
        self._m = module

    def write(self, kind: str, payload: Dict[str, Any]) -> None:
        self._m.write_event(kind, payload)

    def read(self, kind: Optional[str] = None) -> Iterable[Dict[str, Any]]:
        path = self._m.path
        if not path.exists():
            return iter(())

        def _iter() -> Iterable[Dict[str, Any]]:
            malformed = 0
            with path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                    except (TypeError, ValueError):
                        malformed += 1
                        log.warning(
                            "Skipping malformed memory record at %s:%d",
                            path,
                            line_number,
                        )
                        continue
                    if not isinstance(obj, dict):
                        malformed += 1
                        log.warning(
                            "Skipping non-object memory record at %s:%d",
                            path,
                            line_number,
                        )
                        continue
                    if kind is None or obj.get("kind") == kind:
                        yield obj
            if malformed:
                log.warning(
                    "Memory read completed with %d malformed record(s) skipped.",
                    malformed,
                )

        return _iter()


class MemoryModule:
    """Small append-only memory ledger used by the early Velvet runtime."""

    name = "memory"

    def __init__(self, path: str = "memory_events.jsonl") -> None:
        # Relative paths are resolved by the runtime working directory
        # (normally /var/lib/velvet).
        self.path = Path(path)
        self._fp: Optional[Any] = None
        self._write_lock = threading.Lock()
        self.adapter = _FileMemoryAdapter(self)

    def start(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fp = self.path.open("a", encoding="utf-8")
        log.info("Memory module started (path=%s).", self.path)

        reg = get_registry()
        if reg:
            reg.provide(MemoryInterface, self.adapter)

        self.write_event(
            "system",
            {"event": "boot", "msg": "Velvet memory online"},
            source="velvet-ai-core",
            tags=["lifecycle", "boot"],
        )

        bus = get_event_bus()
        if bus:
            bus.emit("memory.started", {"path": str(self.path)})
            bus.emit("memory.provided", {"interface": "MemoryInterface"})

    def stop(self) -> None:
        bus = get_event_bus()
        if bus:
            bus.emit("memory.stopping", {"path": str(self.path)})

        if self._fp:
            self.write_event(
                "system",
                {"event": "shutdown", "msg": "Velvet memory offline"},
                source="velvet-ai-core",
                tags=["lifecycle", "shutdown"],
            )
            with self._write_lock:
                try:
                    self._fp.flush()
                    os.fsync(self._fp.fileno())
                    self._fp.close()
                except OSError:
                    log.exception("Failed to close memory ledger cleanly.")
                finally:
                    self._fp = None

        log.info("Memory module stopped.")
        bus = get_event_bus()
        if bus:
            bus.emit("memory.stopped", {"path": str(self.path)})

    def write_event(
        self,
        kind: str,
        payload: Dict[str, Any],
        source: Optional[str] = None,
        confidence: Optional[float] = None,
        authority_status: Optional[str] = None,
        receipt_id: Optional[str] = None,
        related_event_ids: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if not self._fp:
            raise RuntimeError("memory module is not started")

        record = MemoryRecord(
            kind=kind,
            payload=payload,
            source=source,
            confidence=confidence,
            authority_status=authority_status,
            receipt_id=receipt_id,
            related_event_ids=list(related_event_ids or []),
            tags=list(tags or []),
        )
        event = record.to_dict()
        encoded = json.dumps(event, ensure_ascii=False, separators=(",", ":"))

        with self._write_lock:
            self._fp.write(encoded + "\n")
            self._fp.flush()
            os.fsync(self._fp.fileno())

        bus = get_event_bus()
        if bus:
            bus.emit("memory.event", event)

        return event
