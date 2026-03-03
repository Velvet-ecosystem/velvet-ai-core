# velvet/core/modules/heartbeat.py
from __future__ import annotations

import logging
import threading
import time
from typing import Optional

from velvet.core.context import get_event_bus
from velvet.core.schemas.topics import Topics

log = logging.getLogger("velvet.module.heartbeat")


class HeartbeatModule:
    name = "heartbeat"

    def __init__(self, interval_s: float = 5.0) -> None:
        self.interval = float(interval_s)
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="velvet-heartbeat", daemon=True)
        self._thread.start()
        log.info("Heartbeat module started (interval=%ss).", self.interval)

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        log.info("Heartbeat module stopped.")

    def _loop(self) -> None:
        while self._running:
            bus = get_event_bus()
            if bus:
                bus.emit(Topics.HEARTBEAT, {"ts": time.time()})
            time.sleep(self.interval)
