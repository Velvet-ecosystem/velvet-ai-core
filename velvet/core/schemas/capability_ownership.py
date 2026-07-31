"""Capability ownership contracts for Velvet's Unified-Organ body."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple


class CapabilityAuthority(str, Enum):
    OBSERVE = "OBSERVE"
    PROPOSE = "PROPOSE"
    GOVERNED_CONTROL = "GOVERNED_CONTROL"
    GOVERNED_EMERGENCY = "GOVERNED_EMERGENCY"


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % name)


@dataclass(frozen=True)
class CapabilityOwnership:
    """One durable ownership row. Ownership never bypasses Runtime or Court."""

    capability_name: str
    owning_handmaiden: str
    inputs: Tuple[str, ...]
    outputs: Tuple[str, ...]
    dependencies: Tuple[str, ...]
    fallback_owner: Optional[str]
    authority_level: CapabilityAuthority
    receipt_types: Tuple[str, ...]
    degraded_behavior: str
    forbidden_direct_callers: Tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("capability_name", "owning_handmaiden", "degraded_behavior"):
            _require_text(name, getattr(self, name))
        if self.fallback_owner is not None:
            _require_text("fallback_owner", self.fallback_owner)
        if not isinstance(self.authority_level, CapabilityAuthority):
            object.__setattr__(
                self, "authority_level", CapabilityAuthority(self.authority_level)
            )

    def caller_is_forbidden(self, caller: str) -> bool:
        _require_text("caller", caller)
        return caller in self.forbidden_direct_callers

    def to_dict(self) -> Dict[str, Any]:
        return {
            "capability_name": self.capability_name,
            "owning_handmaiden": self.owning_handmaiden,
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
            "dependencies": list(self.dependencies),
            "fallback_owner": self.fallback_owner,
            "authority_level": self.authority_level.value,
            "receipt_types": list(self.receipt_types),
            "degraded_behavior": self.degraded_behavior,
            "forbidden_direct_callers": list(self.forbidden_direct_callers),
        }
