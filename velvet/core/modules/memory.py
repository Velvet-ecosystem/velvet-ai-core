# velvet/core/modules/memory.py
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from velvet.core.context import get_event_bus, get_registry
from velvet.core.interfaces.memory import MemoryInterface

log = logging.getLogger("velvet.module.memory")


class _FileMemoryAdapter(MemoryInterface):
    """
    Adapter that satisfies MemoryInterface using MemoryModule's file writer.
    Read() is a simple streaming reader for now (good enough for early tooling).
    """

    def __init__(self, module: "MemoryModule") -> None:
        self._m = module

    def write(self, kind: str, payload: Dict[str, Any]) -> None:
        self._m.write_event(kind, payload)

    def read(self, kind: str | None = None) -> Iterable[Dict[str, Any]]:
        # Best-effort streaming read of the JSONL file.
        path = self._m.path
        if not path.exists():
            return []
        def _iter():
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    if not isinstance(obj, dict):
                        continue
                    if kind is None or obj.get("kind") == kind:
                        yield obj
                except Exception:
                    continue
        return _iter()


class MemoryModule:
    name = "memory"

    def __init__(self, path: str = "memory_events.jsonl") -> None:
        # relative to WorkingDirectory (/var/lib/velvet)
        self.path = Path(path)
        self._fp: Optional[Any] = None
        self.adapter = _FileMemoryAdapter(self)

    def start(self) -> None:
        self._fp = self.path.open("a", encoding="utf-8")
        log.info("Memory module started (path=%s).", self.path)

        # Provide memory capability to the registry
        reg = get_registry()
        if reg:
            reg.provide(MemoryInterface, self.adapter)

        # boot receipt
        self.write_event("boot", {"msg": "Velvet memory online"})

        # emit to bus for UI
        bus = get_event_bus()
        if bus:
            bus.emit("memory.started", {"path": str(self.path)})
            bus.emit("memory.provided", {"interface": "MemoryInterface"})

    def stop(self) -> None:
        bus = get_event_bus()
        if bus:
            bus.emit("memory.stopping", {"path": str(self.path)})

        if self._fp:
            self.write_event("shutdown", {"msg": "Velvet memory offline"})
            try:
                self._fp.flush()
                self._fp.close()
            except Exception:
                pass
            self._fp = None

        log.info("Memory module stopped.")

        bus = get_event_bus()
        if bus:
            bus.emit("memory.stopped", {"path": str(self.path)})

    def write_event(self, kind: str, payload: Dict[str, Any]) -> None:
        if not self._fp:
            return

        event = {
            "ts": time.time(),
            "kind": kind,
            "payload": payload,
        }

        self._fp.write(json.dumps(event, ensure_ascii=False) + "\n")
        self._fp.flush()

        # Also publish to the event bus so UI can “listen”
        bus = get_event_bus()
        if bus:
            bus.emit("memory.event", {"kind": kind, "payload": payload})
