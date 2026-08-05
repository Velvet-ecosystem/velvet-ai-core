"""Health and output boundaries for future local vision nodes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class VisionHealth(str, Enum):
    READY = "ready"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass(frozen=True)
class CameraChannelStatus:
    camera_id: str
    online: bool
    timestamp_quality: float
    frame_drop_rate: float
    transport_error_count: int
    temperature_c: float

    def __post_init__(self) -> None:
        if not isinstance(self.camera_id, str) or not self.camera_id.strip():
            raise ValueError("camera_id must be a non-empty string")
        for name in ("timestamp_quality", "frame_drop_rate"):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError("%s must be between 0 and 1" % name)
        if self.transport_error_count < 0:
            raise ValueError("transport_error_count must be non-negative")


@dataclass(frozen=True)
class VisionNodeAssessment:
    health: VisionHealth
    available_cameras: Tuple[str, ...]
    degraded_cameras: Tuple[str, ...]
    health_events: Tuple[str, ...]
    raw_stream_default: bool = False
    authority_granted: bool = False


def assess_vision_node(
    channels: Tuple[CameraChannelStatus, ...],
    *,
    maximum_temperature_c: float = 85.0,
    maximum_drop_rate: float = 0.10,
    minimum_timestamp_quality: float = 0.80,
) -> VisionNodeAssessment:
    available = []
    degraded = []
    events = []

    for channel in channels:
        if not channel.online:
            degraded.append(channel.camera_id)
            events.append("camera_offline:%s" % channel.camera_id)
            continue
        available.append(channel.camera_id)
        if channel.frame_drop_rate > maximum_drop_rate:
            degraded.append(channel.camera_id)
            events.append("frame_drop:%s" % channel.camera_id)
        if channel.timestamp_quality < minimum_timestamp_quality:
            degraded.append(channel.camera_id)
            events.append("timestamp_quality:%s" % channel.camera_id)
        if channel.temperature_c > maximum_temperature_c:
            degraded.append(channel.camera_id)
            events.append("camera_hot:%s" % channel.camera_id)
        if channel.transport_error_count:
            events.append("transport_errors:%s" % channel.camera_id)

    available_names = tuple(sorted(set(available)))
    degraded_names = tuple(sorted(set(degraded)))
    if not available_names:
        health = VisionHealth.FAILED
    elif degraded_names:
        health = VisionHealth.DEGRADED
    else:
        health = VisionHealth.READY

    return VisionNodeAssessment(
        health=health,
        available_cameras=available_names,
        degraded_cameras=degraded_names,
        health_events=tuple(events),
    )
