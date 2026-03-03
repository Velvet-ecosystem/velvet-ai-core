# velvet/core/modules/command_bus.py
from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

from velvet.core.command_router import CommandRouter
from velvet.core.context import get_event_bus
from velvet.core.schemas.topics import Topics

log = logging.getLogger("velvet.module.command_bus")


class CommandBusModule:
    name = "command_bus"

    def __init__(self, path: str = "commands.jsonl", poll_interval_s: float = 0.5) -> None:
        # relative to WorkingDirectory (/var/lib/velvet)
        self.path = Path(path)
        self.poll_interval = float(poll_interval_s)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._offset = 0  # file read position
        self._router = CommandRouter()

    def start(self) -> None:
        # Ensure file exists
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)
        self._offset = self.path.stat().st_size

        self._running = True
        self._thread = threading.Thread(target=self._loop, name="velvet-command-bus", daemon=True)
        self._thread.start()

        log.info("Command bus started (path=%s, poll=%ss).", self.path, self.poll_interval)
        bus = get_event_bus()
        if bus:
            bus.emit(Topics.COMMAND_RECEIVED, {"status": "command_bus.started", "path": str(self.path)})

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        log.info("Command bus stopped.")

        bus = get_event_bus()
        if bus:
            bus.emit(Topics.COMMAND_RECEIVED, {"status": "command_bus.stopped", "path": str(self.path)})

    def _loop(self) -> None:
        while self._running:
            try:
                if not self.path.exists():
                    time.sleep(self.poll_interval)
                    continue

                with self.path.open("r", encoding="utf-8") as f:
                    f.seek(self._offset)
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        cmd = self._parse(line)
                        if cmd:
                            self._handle(cmd)

                    self._offset = f.tell()

            except Exception:
                log.exception("Command bus loop error")

            time.sleep(self.poll_interval)

    def _parse(self, line: str) -> Optional[Dict[str, Any]]:
        try:
            obj = json.loads(line)
            if isinstance(obj, dict) and "cmd" in obj:
                return obj
        except Exception:
            log.exception("Bad command line (not json dict with 'cmd')")
        return None

    def _handle(self, cmd: Dict[str, Any]) -> None:
        log.info("Command received: %s", cmd)

        bus = get_event_bus()
        if bus:
            bus.emit(Topics.COMMAND_RECEIVED, cmd)

        # Route it (router will emit command.ok/command.error + any domain events)
        self._router.handle(cmd)
