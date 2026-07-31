"""Standard health event contract for Velvet modules and nodes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Mapping, Optional

from .sensor_packet import HealthState


class HealthEventType(str, Enum):
    ONLINE = "ONLINE"
    READY = "READY"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    RECOVERING = "RECOVERING"
    RECOVERED = "RECOVERED"
    OFFLINE = "OFFLINE"
    STALE = "STALE"
    CALIBRATION_REQUIRED = "CALIBRATION_REQUIRED"


class HealthSeverity(str, Enum):
    INFO = "INFO"
    NOTICE = "NOTICE"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % name)


@dataclass(frozen=True)
class HealthEvent:
    """Immutable subsystem health transition with diagnostic provenance."""

    event_id: str
    event_type: HealthEventType
    module_id: str
    node_id: str
    owning_handmaiden: str
    timestamp: float
    severity: HealthSeverity
    state_before: HealthState
    state_after: HealthState
    confidence: float
    diagnostic_payload: Mapping[str, Any] = field(default_factory=dict)
    receipt_id: str = ""
    recovery_action: Optional[str] = None
    fallback_owner: Optional[str] = None

    def __post_init__(self) -> None:
        for name in (
            "event_id",
            "module_id",
            "node_id",
            "owning_handmaiden",
            "receipt_id",
        ):
            _require_text(name, getattr(self, name))

        if not isinstance(self.diagnostic_payload, Mapping):
            raise ValueError("diagnostic_payload must be a mapping")
        if self.timestamp < 0:
            raise ValueError("timestamp must be non-negative")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        for name, enum_type in (
            ("event_type", HealthEventType),
            ("severity", HealthSeverity),
            ("state_before", HealthState),
            ("state_after", HealthState),
        ):
            value = getattr(self, name)
            if not isinstance(value, enum_type):
                object.__setattr__(self, name, enum_type(value))

        if self.recovery_action is not None:
            _require_text("recovery_action", self.recovery_action)
        if self.fallback_owner is not None:
            _require_text("fallback_owner", self.fallback_owner)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "module_id": self.module_id,
            "node_id": self.node_id,
            "owning_handmaiden": self.owning_handmaiden,
            "timestamp": float(self.timestamp),
            "severity": self.severity.value,
            "state_before": self.state_before.value,
            "state_after": self.state_after.value,
            "confidence": float(self.confidence),
            "diagnostic_payload": dict(self.diagnostic_payload),
            "receipt_id": self.receipt_id,
            "recovery_action": self.recovery_action,
            "fallback_owner": self.fallback_owner,
        }

    def to_event_protocol(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": "HEALTH_%s" % self.event_type.value,
            "source": self.module_id,
            "family": "health",
            "schema_version": "1.0",
            "timestamp": float(self.timestamp),
            "node_id": self.node_id,
            "organ_name": self.owning_handmaiden,
            "payload": self.to_dict(),
        }
