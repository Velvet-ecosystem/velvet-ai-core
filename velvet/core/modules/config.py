# velvet/core/modules/config.py
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

log = logging.getLogger("velvet.module.config")


class ConfigModule:
    name = "config"

    def __init__(self, path: str = "velvet_config.json") -> None:
        # relative to WorkingDirectory (/var/lib/velvet) by default
        self.path = Path(path)
        self.data: Dict[str, Any] = {}

    def start(self) -> None:
        self.data = self._load_or_default()
        log.info("Config module started (path=%s). Keys=%d", self.path, len(self.data))

    def stop(self) -> None:
        log.info("Config module stopped.")

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def _load_or_default(self) -> Dict[str, Any]:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                log.exception("Failed to parse config; using defaults.")
        # defaults (keep tiny for now)
        return {
            "tick_interval_s": 5,
            "heartbeat_interval_s": 5,
        }
