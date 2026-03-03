# velvet/core/modules/health.py
from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Optional

from velvet.core.context import get_event_bus
from velvet.core.schemas.topics import Topics

log = logging.getLogger("velvet.module.health")


class HealthModule:
    name = "health"

    def __init__(self, path: str = "health.json", interval_s: float = 2.0) -> None:
        # relative to WorkingDirectory (/var/lib/velvet)
        self.path = Path(path)
        self.interval = float(interval_s)
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="velvet-health", daemon=True)
        self._thread.start()
        log.info("Health module started (interval=%ss, path=%s).", self.interval, self.path)

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        log.info("Health module stopped.")

    def _loop(self) -> None:
        while self._running:
            data = {
                "ts": time.time(),
                "status": "ok",
            }

            # Write state file (for external tools / probes)
            try:
                self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            except Exception:
                log.exception("Failed to write health file")

            # Emit state event (for UI)
            bus = get_event_bus()
            if bus:
                bus.emit(Topics.HEALTH_UPDATE, data)

            time.sleep(self.interval)
