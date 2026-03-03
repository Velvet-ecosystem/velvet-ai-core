# velvet/core/context.py
from __future__ import annotations

from typing import Optional

from velvet.core.modules.event_bus import EventBusModule
from velvet.core.registry import Registry

_event_bus: Optional[EventBusModule] = None
_registry: Optional[Registry] = None


def set_event_bus(bus: EventBusModule) -> None:
    global _event_bus
    _event_bus = bus


def get_event_bus() -> Optional[EventBusModule]:
    return _event_bus


def set_registry(reg: Registry) -> None:
    global _registry
    _registry = reg


def get_registry() -> Optional[Registry]:
    return _registry
