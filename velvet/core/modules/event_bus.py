# velvet/core/modules/event_bus.py
from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

from velvet.core.schemas.events import make_event

log = logging.getLogger("velvet.module.event_bus")


class EventBusModule:
    """
    Minimal event bus:
    - emit(topic, data) appends a standard envelope JSON line to events.jsonl
    - safe for UI to tail
    """

    name = "event_bus"

    def __init__(self, path: str = "events.jsonl") -> None:
        self.path = Path(path)
        self._fp: Optional[Any] = None
        self._lock = threading.Lock()

    def start(self) -> None:
        # Ensure file exists and open append
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fp = self.path.open("a", encoding="utf-8")
        log.info("Event bus started (path=%s).", self.path)

        # boot event
        self.emit("event_bus.started", {"path": str(self.path)})

    def stop(self) -> None:
        # stopping event (best-effort)
        try:
            self.emit("event_bus.stopping", {"path": str(self.path)})
        except Exception:
            pass

        with self._lock:
            if self._fp:
                try:
                    self._fp.flush()
                    self._fp.close()
                except Exception:
                    pass
                self._fp = None

        log.info("Event bus stopped.")

    def emit(self, topic: str, data: Dict[str, Any]) -> None:
        """
        Append one standard-envelope JSON line:
          {"ts":..., "topic":"...", "data":{...}}
        """
        if not isinstance(data, dict):
            # Keep bus strict; callers must send objects
            data = {"value": data}

        evt = make_event(topic, data).to_dict()
        line = json.dumps(evt, ensure_ascii=False)

        with self._lock:
            if not self._fp:
                # If emit happens before start(), fail quietly (or raise later)
                return
            self._fp.write(line + "\n")
            self._fp.flush()
