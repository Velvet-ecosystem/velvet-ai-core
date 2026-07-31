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

__all__ = [
    "CapabilityAuthority",
    "CapabilityOwnership",
    "HealthEvent",
    "HealthEventType",
    "HealthSeverity",
    "HealthState",
    "NodeCapabilityManifest",
    "SensorPacket",
    "SourceClock",
    "VehicleInterfaceAuthority",
    "VehicleInterfaceContract",
]
