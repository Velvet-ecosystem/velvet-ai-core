# SPDX-License-Identifier: GPL-3.0-only
"""Resolve bounded conversation facts from Runtime body-state snapshots.

The resolver consumes the read-only ``velvet.runtime.body_state_snapshot.v1``
shape through an injected provider.  It never reads Runtime files directly,
never infers actuation, and never turns ignition or charging voltage into an
engine-running claim.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional, Sequence, Tuple

from .conversation_ingress import (
    ConversationMeaningKind,
    ConversationWorkRequest,
    GroundedConversationMeaning,
)

BODY_STATE_SNAPSHOT_SCHEMA = "velvet.runtime.body_state_snapshot.v1"
SnapshotProvider = Callable[[], Mapping[str, Any]]
Clock = Callable[[], float]


@dataclass(frozen=True)
class BodyFactSpec:
    fact_id: str
    sensor_type: str
    payload_key: str
    unit: Optional[str] = None
    requires_valid_fix: bool = False


_FACTS = {
    "cabin.temperature": BodyFactSpec(
        "cabin.temperature", "environmental_conditions", "cabin_temperature_c", "C"
    ),
    "outside.temperature": BodyFactSpec(
        "outside.temperature", "environmental_conditions", "outside_temperature_c", "C"
    ),
    "cabin.humidity": BodyFactSpec(
        "cabin.humidity", "environmental_conditions", "relative_humidity_percent", "%"
    ),
    "cabin.ambient_light": BodyFactSpec(
        "cabin.ambient_light", "environmental_conditions", "ambient_light_lux", "lux"
    ),
    "ignition.state": BodyFactSpec(
        "ignition.state", "vehicle_power_state", "ignition_state"
    ),
    "vehicle.voltage": BodyFactSpec(
        "vehicle.voltage", "vehicle_power_state", "voltage_v", "V"
    ),
    "vehicle.speed": BodyFactSpec(
        "vehicle.speed", "gnss_fix", "speed_kmh", "km/h", requires_valid_fix=True
    ),
}


class BodySnapshotConversationResolver:
    """Ground selected owner-facing facts in the current body snapshot."""

    def __init__(
        self,
        snapshot_provider: SnapshotProvider,
        *,
        wall_clock: Optional[Clock] = None,
    ) -> None:
        if not callable(snapshot_provider):
            raise TypeError("snapshot_provider must be callable")
        if wall_clock is not None and not callable(wall_clock):
            raise TypeError("wall_clock must be callable")
        self._snapshot_provider = snapshot_provider
        self._wall_clock = wall_clock or time.time

    def __call__(self, request: ConversationWorkRequest) -> GroundedConversationMeaning:
        if not isinstance(request, ConversationWorkRequest):
            raise TypeError("request must be ConversationWorkRequest")

        if request.requires_authority_check:
            return GroundedConversationMeaning(
                response_kind=ConversationMeaningKind.AUTHORITY_REQUIRED,
                confidence=1.0,
                qualifiers=("runtime-authorization-required",),
            )

        fact_id = _requested_fact_id(request.text)
        if fact_id is None:
            return GroundedConversationMeaning(
                response_kind=ConversationMeaningKind.UNAVAILABLE,
                confidence=0.0,
                qualifiers=("unsupported-body-fact",),
            )

        snapshot = self._snapshot_provider()
        normalized = validate_body_snapshot(snapshot)
        spec = _FACTS[fact_id]
        record = _newest_sensor_record(normalized["records"], spec.sensor_type)
        if record is None:
            return _unavailable("sensor-not-present")

        sensor = record["payload"]
        data = sensor["payload"]
        if spec.requires_valid_fix and data.get("has_fix") is not True:
            return _unavailable("navigation-fix-unavailable")

        value = data.get(spec.payload_key)
        if value is None:
            return _unavailable("fact-value-unavailable")
        _require_scalar(value)

        confidence = _confidence(sensor.get("confidence", 0.0))
        qualifiers = []
        now = _non_negative_number(self._wall_clock(), "wall clock")
        timestamp = _non_negative_number(sensor.get("timestamp"), "sensor timestamp")
        stale_after_ms = _positive_integer(sensor.get("stale_after_ms"), "stale_after_ms")
        age_ms = max(0.0, now - timestamp) * 1000.0
        if age_ms > float(stale_after_ms):
            qualifiers.append("stale")

        source_refs = _source_refs(sensor)
        return GroundedConversationMeaning(
            response_kind=ConversationMeaningKind.FACT,
            confidence=confidence,
            fact_id=spec.fact_id,
            value=value,
            unit=spec.unit,
            qualifiers=tuple(qualifiers),
            source_refs=source_refs,
        )


def validate_body_snapshot(snapshot: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate the bounded Runtime snapshot posture required by Core."""

    if not isinstance(snapshot, Mapping):
        raise TypeError("body snapshot must be a mapping")
    if snapshot.get("schema") != BODY_STATE_SNAPSHOT_SCHEMA:
        raise ValueError("unsupported body snapshot schema")
    if snapshot.get("read_only") is not True:
        raise ValueError("body snapshot must be read-only")
    if snapshot.get("authority") != "none":
        raise ValueError("body snapshot cannot carry authority")
    if snapshot.get("actuation_granted") is not False:
        raise ValueError("body snapshot cannot grant actuation")
    if snapshot.get("actuation_performed") is not False:
        raise ValueError("body snapshot cannot claim actuation")
    records = snapshot.get("records")
    if not isinstance(records, list):
        raise ValueError("body snapshot records must be a list")
    if len(records) > 8192:
        raise ValueError("body snapshot record count exceeds resolver bound")

    for record in records:
        _validate_record(record)
    return snapshot


def _validate_record(record: Any) -> None:
    if not isinstance(record, Mapping):
        raise ValueError("body snapshot record must be a mapping")
    family = record.get("family")
    if family not in {"sensor", "health"}:
        raise ValueError("body snapshot record family is invalid")
    payload = record.get("payload")
    if not isinstance(payload, Mapping):
        raise ValueError("body snapshot record payload must be a mapping")
    module_id = payload.get("module_id")
    if not isinstance(module_id, str) or not module_id.strip():
        raise ValueError("body snapshot record module_id is invalid")
    timestamp = payload.get("timestamp")
    _non_negative_number(timestamp, "record timestamp")

    if family == "sensor":
        sensor_type = payload.get("sensor_type")
        if not isinstance(sensor_type, str) or not sensor_type.strip():
            raise ValueError("body snapshot sensor_type is invalid")
        if not isinstance(payload.get("payload"), Mapping):
            raise ValueError("body snapshot sensor payload must be a mapping")
        _confidence(payload.get("confidence", 0.0))
        _positive_integer(payload.get("stale_after_ms"), "stale_after_ms")


def _newest_sensor_record(
    records: Sequence[Mapping[str, Any]], sensor_type: str
) -> Optional[Mapping[str, Any]]:
    newest = None
    newest_timestamp = -1.0
    for record in records:
        if record.get("family") != "sensor":
            continue
        payload = record.get("payload")
        if not isinstance(payload, Mapping):
            continue
        if payload.get("sensor_type") != sensor_type:
            continue
        timestamp = float(payload.get("timestamp", -1.0))
        if timestamp >= newest_timestamp:
            newest = record
            newest_timestamp = timestamp
    return newest


def _requested_fact_id(text: str) -> Optional[str]:
    lower = " ".join(text.casefold().replace("?", " ").split())

    # Do not collapse ignition evidence into an engine-running claim.
    if any(
        phrase in lower
        for phrase in (
            "engine running",
            "engine on",
            "car running",
            "vehicle running",
            "motor running",
        )
    ):
        return None

    if _contains_any(
        lower,
        (
            "outside temperature",
            "outside temp",
            "temperature outside",
            "temp outside",
            "how hot is it outside",
            "how cold is it outside",
        ),
    ):
        return "outside.temperature"

    if _contains_any(
        lower,
        (
            "cabin temperature",
            "cabin temp",
            "inside temperature",
            "inside temp",
            "interior temperature",
            "interior temp",
            "how hot is it in here",
            "how cold is it in here",
        ),
    ):
        return "cabin.temperature"

    if "humidity" in lower:
        return "cabin.humidity"
    if _contains_any(lower, ("ambient light", "light level", "how bright", "lux")):
        return "cabin.ambient_light"
    if _contains_any(lower, ("ignition", "key on", "key off")):
        return "ignition.state"
    if _contains_any(
        lower,
        (
            "vehicle voltage",
            "battery voltage",
            "supply voltage",
            "system voltage",
            "what voltage",
        ),
    ):
        return "vehicle.voltage"
    if _contains_any(lower, ("vehicle speed", "current speed", "how fast", "speed are we")):
        return "vehicle.speed"
    return None


def _contains_any(text: str, phrases: Tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


def _source_refs(sensor: Mapping[str, Any]) -> Tuple[str, ...]:
    refs = []
    receipt = sensor.get("receipt_id")
    if isinstance(receipt, str) and receipt.strip():
        refs.append("receipt:%s" % receipt.strip())
    raw = sensor.get("raw_reference")
    if isinstance(raw, str) and raw.strip():
        refs.append(raw.strip())
    return tuple(refs[:4])


def _unavailable(reason: str) -> GroundedConversationMeaning:
    return GroundedConversationMeaning(
        response_kind=ConversationMeaningKind.UNAVAILABLE,
        confidence=0.0,
        qualifiers=(reason,),
    )


def _confidence(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("sensor confidence must be numeric")
    number = float(value)
    if not 0.0 <= number <= 1.0:
        raise ValueError("sensor confidence must be between 0 and 1")
    return number


def _non_negative_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s must be numeric" % label)
    number = float(value)
    if number < 0.0:
        raise ValueError("%s must be non-negative" % label)
    return number


def _positive_integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("%s must be a positive integer" % label)
    return value


def _require_scalar(value: Any) -> None:
    if isinstance(value, (dict, list, tuple, set)):
        raise ValueError("body fact value must be scalar")
    if isinstance(value, str) and len(value) > 512:
        raise ValueError("body fact text exceeds maximum length")
