# velvet/core/modules/registry_module.py
from __future__ import annotations

import logging

from velvet.core.context import set_registry
from velvet.core.registry import Registry

log = logging.getLogger("velvet.module.registry")


class RegistryModule:
    name = "registry"

    def __init__(self) -> None:
        self.registry = Registry()

    def start(self) -> None:
        set_registry(self.registry)
        log.info("Registry module started.")

    def stop(self) -> None:
        log.info("Registry module stopped.")
