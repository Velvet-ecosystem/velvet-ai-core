"""Deterministic lifecycle contract for Velvet modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Mapping, Tuple

from .schemas.health_event import HealthEventType


class ModuleLifecycleState(str, Enum):
    DISCOVERED = "DISCOVERED"
    CONFIGURED = "CONFIGURED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    RECOVERING = "RECOVERING"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    OFFLINE = "OFFLINE"


DEFAULT_TRANSITIONS = {
    ModuleLifecycleState.DISCOVERED: (ModuleLifecycleState.CONFIGURED,),
    ModuleLifecycleState.CONFIGURED: (
        ModuleLifecycleState.INITIALIZING,
        ModuleLifecycleState.SHUTTING_DOWN,
    ),
    ModuleLifecycleState.INITIALIZING: (
        ModuleLifecycleState.READY,
        ModuleLifecycleState.DEGRADED,
        ModuleLifecycleState.FAILED,
    ),
    ModuleLifecycleState.READY: (
        ModuleLifecycleState.ACTIVE,
        ModuleLifecycleState.DEGRADED,
        ModuleLifecycleState.SHUTTING_DOWN,
    ),
    ModuleLifecycleState.ACTIVE: (
        ModuleLifecycleState.DEGRADED,
        ModuleLifecycleState.FAILED,
        ModuleLifecycleState.SHUTTING_DOWN,
    ),
    ModuleLifecycleState.DEGRADED: (
        ModuleLifecycleState.ACTIVE,
        ModuleLifecycleState.FAILED,
        ModuleLifecycleState.RECOVERING,
        ModuleLifecycleState.SHUTTING_DOWN,
    ),
    ModuleLifecycleState.FAILED: (
        ModuleLifecycleState.RECOVERING,
        ModuleLifecycleState.SHUTTING_DOWN,
        ModuleLifecycleState.OFFLINE,
    ),
    ModuleLifecycleState.RECOVERING: (
        ModuleLifecycleState.READY,
        ModuleLifecycleState.DEGRADED,
        ModuleLifecycleState.FAILED,
    ),
    ModuleLifecycleState.SHUTTING_DOWN: (ModuleLifecycleState.OFFLINE,),
    ModuleLifecycleState.OFFLINE: (
        ModuleLifecycleState.DISCOVERED,
        ModuleLifecycleState.INITIALIZING,
    ),
}


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % name)


@dataclass(frozen=True)
class LifecycleStatePolicy:
    state: ModuleLifecycleState
    entry_condition: str
    exit_condition: str
    timeout_ms: int
    receipt_type: str
    health_event_type: HealthEventType
    owning_handmaiden: str
    fallback_behavior: str
    authority_allowed: bool = False

    def __post_init__(self) -> None:
        for name in (
            "entry_condition",
            "exit_condition",
            "receipt_type",
            "owning_handmaiden",
            "fallback_behavior",
        ):
            _require_text(name, getattr(self, name))
        if int(self.timeout_ms) < 0:
            raise ValueError("timeout_ms must be non-negative")
        if not isinstance(self.state, ModuleLifecycleState):
            object.__setattr__(self, "state", ModuleLifecycleState(self.state))
        if not isinstance(self.health_event_type, HealthEventType):
            object.__setattr__(
                self,
                "health_event_type",
                HealthEventType(self.health_event_type),
            )


@dataclass(frozen=True)
class ModuleLifecycleContract:
    """Complete lifecycle policy. Lifecycle permission is necessary, never sufficient."""

    module_id: str
    policies: Mapping[ModuleLifecycleState, LifecycleStatePolicy]
    transitions: Mapping[
        ModuleLifecycleState, Tuple[ModuleLifecycleState, ...]
    ] = field(default_factory=lambda: dict(DEFAULT_TRANSITIONS))

    def __post_init__(self) -> None:
        _require_text("module_id", self.module_id)
        missing = set(ModuleLifecycleState).difference(self.policies)
        if missing:
            raise ValueError(
                "missing lifecycle policies: %s"
                % ", ".join(sorted(state.value for state in missing))
            )

    def policy(self, state: ModuleLifecycleState) -> LifecycleStatePolicy:
        normalized = (
            state
            if isinstance(state, ModuleLifecycleState)
            else ModuleLifecycleState(state)
        )
        return self.policies[normalized]

    def can_transition(
        self,
        current: ModuleLifecycleState,
        target: ModuleLifecycleState,
    ) -> bool:
        current_state = (
            current
            if isinstance(current, ModuleLifecycleState)
            else ModuleLifecycleState(current)
        )
        target_state = (
            target
            if isinstance(target, ModuleLifecycleState)
            else ModuleLifecycleState(target)
        )
        return target_state in self.transitions.get(current_state, ())

    def require_transition(
        self,
        current: ModuleLifecycleState,
        target: ModuleLifecycleState,
    ) -> None:
        if not self.can_transition(current, target):
            raise ValueError(
                "illegal lifecycle transition: %s -> %s"
                % (
                    ModuleLifecycleState(current).value,
                    ModuleLifecycleState(target).value,
                )
            )


def standard_lifecycle_contract(
    module_id: str,
    owning_handmaiden: str,
    fallback_behavior: str = "fail-closed and emit health receipt",
    timeout_ms: int = 5000,
) -> ModuleLifecycleContract:
    """Create a conservative complete contract for a new module."""

    _require_text("module_id", module_id)
    _require_text("owning_handmaiden", owning_handmaiden)
    _require_text("fallback_behavior", fallback_behavior)

    health_by_state = {
        ModuleLifecycleState.DISCOVERED: HealthEventType.ONLINE,
        ModuleLifecycleState.CONFIGURED: HealthEventType.ONLINE,
        ModuleLifecycleState.INITIALIZING: HealthEventType.ONLINE,
        ModuleLifecycleState.READY: HealthEventType.READY,
        ModuleLifecycleState.ACTIVE: HealthEventType.READY,
        ModuleLifecycleState.DEGRADED: HealthEventType.DEGRADED,
        ModuleLifecycleState.FAILED: HealthEventType.FAILED,
        ModuleLifecycleState.RECOVERING: HealthEventType.RECOVERING,
        ModuleLifecycleState.SHUTTING_DOWN: HealthEventType.OFFLINE,
        ModuleLifecycleState.OFFLINE: HealthEventType.OFFLINE,
    }

    policies: Dict[ModuleLifecycleState, LifecycleStatePolicy] = {}
    for state in ModuleLifecycleState:
        policies[state] = LifecycleStatePolicy(
            state=state,
            entry_condition="%s entry condition satisfied" % state.value,
            exit_condition="%s exit condition satisfied" % state.value,
            timeout_ms=timeout_ms,
            receipt_type="MODULE_LIFECYCLE_%s" % state.value,
            health_event_type=health_by_state[state],
            owning_handmaiden=owning_handmaiden,
            fallback_behavior=fallback_behavior,
            authority_allowed=(state == ModuleLifecycleState.ACTIVE),
        )

    return ModuleLifecycleContract(module_id=module_id, policies=policies)
