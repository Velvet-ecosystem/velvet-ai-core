"""Node capability manifest contract for Velvet's distributed body."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Tuple


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % name)


@dataclass(frozen=True)
class NodeCapabilityManifest:
    """A node passport describing capacity, ownership, limits, and safe failure."""

    node_id: str
    display_name: str
    hardware_model: str
    operating_system: str
    compute_limits: Mapping[str, Any]
    memory_limits: Mapping[str, Any]
    storage_limits: Mapping[str, Any]
    network_interfaces: Tuple[str, ...] = ()
    attached_sensors: Tuple[str, ...] = ()
    controlled_outputs: Tuple[str, ...] = ()
    allowed_capabilities: Tuple[str, ...] = ()
    forbidden_capabilities: Tuple[str, ...] = ()
    owning_handmaiden: str = ""
    fallback_owner: Optional[str] = None
    heartbeat_interval_ms: int = 1000
    update_method: str = "physical-presence-only"
    receipt_types: Tuple[str, ...] = ()
    failure_behavior: str = "fail-closed"
    safe_shutdown_behavior: str = "emit receipt and remove authority"

    def __post_init__(self) -> None:
        for name in (
            "node_id",
            "display_name",
            "hardware_model",
            "operating_system",
            "owning_handmaiden",
            "update_method",
            "failure_behavior",
            "safe_shutdown_behavior",
        ):
            _require_text(name, getattr(self, name))

        for name in ("compute_limits", "memory_limits", "storage_limits"):
            if not isinstance(getattr(self, name), Mapping):
                raise ValueError("%s must be a mapping" % name)

        if int(self.heartbeat_interval_ms) <= 0:
            raise ValueError("heartbeat_interval_ms must be positive")

        allowed = set(self.allowed_capabilities)
        forbidden = set(self.forbidden_capabilities)
        overlap = sorted(allowed.intersection(forbidden))
        if overlap:
            raise ValueError(
                "capabilities cannot be both allowed and forbidden: %s"
                % ", ".join(overlap)
            )

        if self.fallback_owner is not None:
            _require_text("fallback_owner", self.fallback_owner)

    def permits(self, capability: str) -> bool:
        _require_text("capability", capability)
        return (
            capability in self.allowed_capabilities
            and capability not in self.forbidden_capabilities
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "display_name": self.display_name,
            "hardware_model": self.hardware_model,
            "operating_system": self.operating_system,
            "compute_limits": dict(self.compute_limits),
            "memory_limits": dict(self.memory_limits),
            "storage_limits": dict(self.storage_limits),
            "network_interfaces": list(self.network_interfaces),
            "attached_sensors": list(self.attached_sensors),
            "controlled_outputs": list(self.controlled_outputs),
            "allowed_capabilities": list(self.allowed_capabilities),
            "forbidden_capabilities": list(self.forbidden_capabilities),
            "owning_handmaiden": self.owning_handmaiden,
            "fallback_owner": self.fallback_owner,
            "heartbeat_interval_ms": int(self.heartbeat_interval_ms),
            "update_method": self.update_method,
            "receipt_types": list(self.receipt_types),
            "failure_behavior": self.failure_behavior,
            "safe_shutdown_behavior": self.safe_shutdown_behavior,
        }
