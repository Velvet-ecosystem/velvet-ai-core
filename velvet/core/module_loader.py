# velvet/core/module_loader.py
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Dict, Optional

log = logging.getLogger("velvet.module_loader")


@dataclass
class Module:
    name: str
    start: Callable[[], None]
    stop: Callable[[], None]


class ModuleLoader:
    """
    Very small lifecycle manager:
    - register modules
    - start them in registration order
    - stop them in reverse order
    """

    def __init__(self) -> None:
        self._modules: Dict[str, Module] = {}
        self._start_order: list[str] = []
        self._running = False

    def register(self, name: str, start: Callable[[], None], stop: Callable[[], None]) -> None:
        if name in self._modules:
            raise ValueError(f"Module already registered: {name}")
        self._modules[name] = Module(name=name, start=start, stop=stop)
        self._start_order.append(name)
        log.info("Registered module: %s", name)

    def start_all(self) -> None:
        if self._running:
            return

        started: list[str] = []
        try:
            for name in self._start_order:
                log.info("Starting module: %s", name)
                self._modules[name].start()
                started.append(name)
            self._running = True
        except Exception:
            log.exception("Module start failed; rolling back started modules.")
            for name in reversed(started):
                try:
                    log.info("Stopping module after failed start: %s", name)
                    self._modules[name].stop()
                except Exception:
                    log.exception("Rollback stop failed for module: %s", name)
            self._running = False
            raise

    def stop_all(self) -> None:
        if not self._running:
            return
        for name in reversed(self._start_order):
            try:
                log.info("Stopping module: %s", name)
                self._modules[name].stop()
            except Exception:
                log.exception("Error stopping module: %s", name)
        self._running = False
