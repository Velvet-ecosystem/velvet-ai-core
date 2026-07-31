"""Standard sensor packet contract for Velvet's distributed body."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Mapping, Optional


class HealthState(str, Enum):
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    RECOVERING = "RECOVERING"
    RECOVERED = "RECOVERED"
    UNKNOWN = "UNKNOWN"


class SourceClock(str, Enum):
    WALL = "wall"
    MONOTONIC = "monotonic"
    GNSS = "gnss"
    VEHICLE = "vehicle"
    DEVICE = "device"
    UNKNOWN = "unknown"


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % name)


@dataclass(frozen=True)
class SensorPacket:
    """One immutable observation emitted by a physical or simulated sensor."""

    module_id: str
    node_id: str
    owning_handmaiden: str
    timestamp: float
    monotonic_time: float
    sensor_type: str
    interface_type: str
    health_state: HealthState
    confidence: float
    payload: Mapping[str, Any] = field(default_factory=dict)
    receipt_id: str = ""
    source_clock: SourceClock = SourceClock.UNKNOWN
    stale_after_ms: int = 1000
    calibration_version: str = "unversioned"
    degraded_reason: Optional[str] = None
    raw_reference: Optional[str] = None

    def __post_init__(self) -> None:
        for name in (
            "module_id",
            "node_id",
            "owning_handmaiden",
            "sensor_type",
            "interface_type",
            "receipt_id",
            "calibration_version",
        ):
            _require_text(name, getattr(self, name))

        if not isinstance(self.payload, Mapping):
            raise ValueError("payload must be a mapping")
        if self.timestamp < 0 or self.monotonic_time < 0:
            raise ValueError("timestamps must be non-negative")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if int(self.stale_after_ms) <= 0:
            raise ValueError("stale_after_ms must be positive")

        if not isinstance(self.health_state, HealthState):
            object.__setattr__(self, "health_state", HealthState(self.health_state))
        if not isinstance(self.source_clock, SourceClock):
            object.__setattr__(self, "source_clock", SourceClock(self.source_clock))

        if self.degraded_reason is not None:
            _require_text("degraded_reason", self.degraded_reason)
        if self.raw_reference is not None:
            _require_text("raw_reference", self.raw_reference)

    def is_stale(self, now_monotonic: float) -> bool:
        if now_monotonic < self.monotonic_time:
            return False
        age_ms = (now_monotonic - self.monotonic_time) * 1000.0
        return age_ms > float(self.stale_after_ms)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_id": self.module_id,
            "node_id": self.node_id,
            "owning_handmaiden": self.owning_handmaiden,
            "timestamp": float(self.timestamp),
            "monotonic_time": float(self.monotonic_time),
            "sensor_type": self.sensor_type,
            "interface_type": self.interface_type,
            "health_state": self.health_state.value,
            "confidence": float(self.confidence),
            "payload": dict(self.payload),
            "receipt_id": self.receipt_id,
            "source_clock": self.source_clock.value,
            "stale_after_ms": int(self.stale_after_ms),
            "calibration_version": self.calibration_version,
            "degraded_reason": self.degraded_reason,
            "raw_reference": self.raw_reference,
        }

    def to_event_protocol(self) -> Dict[str, Any]:
        """Create the standard observation record consumed by Event Protocol."""

        return {
            "event_id": self.receipt_id,
            "event_type": "SENSOR_PACKET_OBSERVED",
            "source": self.module_id,
            "family": "sensor",
            "schema_version": "1.0",
            "timestamp": float(self.timestamp),
            "node_id": self.node_id,
            "organ_name": self.owning_handmaiden,
            "payload": self.to_dict(),
        }
