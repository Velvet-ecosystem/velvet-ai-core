"""Safe projection of sensor evidence into descriptive world snapshots.

Sensor packets provide observations. Explicit bindings decide which entity and
state namespace receive that evidence. Projection never grants authority,
executes work, infers identity, or creates spatial relationships.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Tuple

from .schemas.sensor_packet import HealthState, SensorPacket
from .schemas.world_model import (
    EntityIdentity,
    EntityLifecycle,
    TemporalState,
    WorldEntity,
)


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % name)


@dataclass(frozen=True)
class SensorEntityBinding:
    """Configuration-owned link between one sensor module and one entity."""

    module_id: str
    entity_id: str
    state_namespace: str
    roles: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("module_id", "entity_id", "state_namespace"):
            _require_text(name, getattr(self, name))
        for role in self.roles:
            _require_text("role", role)


class WorldModelProjector:
    """Create immutable world snapshots from bound sensor observations."""

    def project_sensor_packet(
        self,
        packet: SensorPacket,
        binding: SensorEntityBinding,
        identity: EntityIdentity,
        received_at: float,
        now_monotonic: Optional[float] = None,
        current: Optional[WorldEntity] = None,
        sequence: Optional[int] = None,
    ) -> WorldEntity:
        if packet.module_id != binding.module_id:
            raise ValueError("sensor packet module does not match binding")
        if identity.entity_id != binding.entity_id:
            raise ValueError("identity does not match binding entity")
        if current is not None and current.entity_id != binding.entity_id:
            raise ValueError("current world entity does not match binding entity")
        if float(received_at) < 0:
            raise ValueError("received_at must be non-negative")

        stale = (
            packet.is_stale(now_monotonic)
            if now_monotonic is not None
            else False
        )

        state = dict(current.state) if current is not None else {}
        state[binding.state_namespace] = {
            "payload": dict(packet.payload),
            "sensor_type": packet.sensor_type,
            "interface_type": packet.interface_type,
            "module_id": packet.module_id,
            "node_id": packet.node_id,
            "owning_handmaiden": packet.owning_handmaiden,
            "health_state": packet.health_state.value,
            "confidence": float(packet.confidence),
            "calibration_version": packet.calibration_version,
            "degraded_reason": packet.degraded_reason,
            "raw_reference": packet.raw_reference,
            "observation_stale": stale,
        }

        receipts = list(current.source_receipt_ids) if current is not None else []
        if packet.receipt_id not in receipts:
            receipts.append(packet.receipt_id)

        roles = list(current.roles) if current is not None else []
        for role in binding.roles:
            if role not in roles:
                roles.append(role)

        temporal = TemporalState(
            observed_at=float(packet.timestamp),
            received_at=float(received_at),
            monotonic_time=float(packet.monotonic_time),
            valid_from=float(packet.timestamp),
            valid_until=None,
            stale_after_ms=int(packet.stale_after_ms),
            sequence=sequence,
            estimated=False,
            disputed=False,
        )

        return WorldEntity(
            identity=identity,
            temporal=temporal,
            lifecycle=self._lifecycle_for(packet.health_state, stale),
            roles=tuple(roles),
            state=state,
            spatial_relations=(
                current.spatial_relations if current is not None else ()
            ),
            source_receipt_ids=tuple(receipts),
        )

    @staticmethod
    def _lifecycle_for(
        health_state: HealthState,
        stale: bool,
    ) -> EntityLifecycle:
        if stale:
            return EntityLifecycle.DEGRADED
        if health_state in (HealthState.ONLINE, HealthState.RECOVERED):
            return EntityLifecycle.ACTIVE
        if health_state in (HealthState.DEGRADED, HealthState.RECOVERING):
            return EntityLifecycle.DEGRADED
        if health_state == HealthState.FAILED:
            return EntityLifecycle.MISSING
        return EntityLifecycle.UNKNOWN
