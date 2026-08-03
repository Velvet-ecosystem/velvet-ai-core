# velvet/core/schemas/__init__.py
"""Shared, dependency-free data contracts for Velvet's distributed body."""

from .capability_ownership import CapabilityAuthority, CapabilityOwnership
from .health_event import HealthEvent, HealthEventType, HealthSeverity
from .node_manifest import NodeCapabilityManifest
from .sensor_packet import HealthState, SensorPacket, SourceClock
from .vehicle_interface import (
    VehicleInterfaceAuthority,
    VehicleInterfaceContract,
)
from .world_model import (
    EntityIdentity,
    EntityLifecycle,
    IdentityEvidence,
    IdentityStatus,
    SpatialRelation,
    SpatialRelationType,
    TemporalState,
    WorldEntity,
)

__all__ = [
    "CapabilityAuthority",
    "CapabilityOwnership",
    "EntityIdentity",
    "EntityLifecycle",
    "HealthEvent",
    "HealthEventType",
    "HealthSeverity",
    "HealthState",
    "IdentityEvidence",
    "IdentityStatus",
    "NodeCapabilityManifest",
    "SensorPacket",
    "SourceClock",
    "SpatialRelation",
    "SpatialRelationType",
    "TemporalState",
    "VehicleInterfaceAuthority",
    "VehicleInterfaceContract",
    "WorldEntity",
]
