"""Consume standard sensor packets into presence fusion and evidence receipts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional, Tuple

from velvet.core.presence_fusion import (
    PresenceFusionResult,
    PresenceObservation,
    PresencePurpose,
    fuse_presence,
)

_REQUIRED_PACKET_FIELDS = (
    "module_id",
    "node_id",
    "timestamp",
    "monotonic_time",
    "sensor_type",
    "interface_type",
    "health_state",
    "confidence",
    "payload",
    "receipt_id",
    "source_clock",
    "stale_after_ms",
    "calibration_version",
)


@dataclass(frozen=True)
class PresencePipelineResult:
    fusion: PresenceFusionResult
    receipt_envelope: Mapping[str, Any]
    simulated_contributors: Tuple[str, ...]
    physical_unlock_allowed: bool
    physical_refusal_reason: str
    authority_granted: bool = False


def fuse_sensor_packets(
    packets: Iterable[Mapping[str, Any]],
    *,
    purpose: PresencePurpose,
    zone: str,
    now: float,
    minimum_sources: Optional[int] = None,
) -> PresencePipelineResult:
    observations = []
    simulated_by_source = {}
    input_receipt_ids = []
    parse_rejections = []

    for packet in packets:
        try:
            observation, simulated, receipt_id = _observation_from_packet(packet)
        except (TypeError, ValueError, KeyError) as exc:
            module_id = (
                packet.get("module_id", "unknown")
                if isinstance(packet, Mapping)
                else "unknown"
            )
            parse_rejections.append(
                (str(module_id), "invalid_packet:%s" % exc)
            )
            continue
        observations.append(observation)
        simulated_by_source[observation.presence_source] = simulated
        input_receipt_ids.append(receipt_id)

    fusion = fuse_presence(
        observations,
        purpose=purpose,
        zone=zone,
        now=float(now),
        minimum_sources=minimum_sources,
    )
    simulated = tuple(
        source
        for source in fusion.contributing_sources
        if simulated_by_source.get(source, False)
    )

    if purpose != PresencePurpose.ACCESS:
        refusal = "court_authorization_required"
    elif simulated:
        refusal = "simulated_presence_cannot_unlock_physical_target"
    elif not fusion.source_diversity_met or fusion.confidence <= 0.0:
        refusal = "insufficient_presence_evidence"
    else:
        refusal = "court_authorization_required"

    rejected = tuple(fusion.rejected_sources) + tuple(parse_rejections)
    accepted = bool(fusion.contributing_sources) and fusion.confidence > 0.0
    envelope = {
        "event_type": (
            "PRESENCE_FUSION_ACCEPTED"
            if accepted
            else "PRESENCE_FUSION_REJECTED"
        ),
        "source": "velvet-ai-core.presence-fusion",
        "subject_id": zone,
        "payload": {
            "state": "accepted" if accepted else "rejected",
            "purpose": purpose.value,
            "zone": zone,
            "confidence": fusion.confidence,
            "source_diversity_met": fusion.source_diversity_met,
            "contributing_sources": fusion.contributing_sources,
            "rejected_sources": rejected,
            "simulated_contributors": simulated,
            "input_receipt_ids": tuple(input_receipt_ids),
            "physical_unlock_allowed": False,
            "physical_refusal_reason": refusal,
            "authority_granted": False,
        },
    }
    return PresencePipelineResult(
        fusion=fusion,
        receipt_envelope=envelope,
        simulated_contributors=simulated,
        physical_unlock_allowed=False,
        physical_refusal_reason=refusal,
    )


def _observation_from_packet(packet: Mapping[str, Any]):
    if not isinstance(packet, Mapping):
        raise TypeError("sensor packet must be a mapping")
    missing = [
        field for field in _REQUIRED_PACKET_FIELDS if field not in packet
    ]
    if missing:
        raise ValueError("missing fields: %s" % ",".join(missing))

    payload = packet["payload"]
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")

    health = str(packet["health_state"]).upper()
    failure_mode = None if health == "ONLINE" else "sensor_%s" % health.lower()
    permitted = payload.get("permitted_purposes", ())
    purposes = tuple(PresencePurpose(value) for value in permitted)
    source = _required_text(payload, "source_id")
    interface_type = _required_text(packet, "interface_type")
    simulated = bool(payload.get("simulated", False)) or (
        "simulated" in interface_type.lower()
    )
    timestamp = float(packet["timestamp"])
    stale_after_ms = int(packet["stale_after_ms"])
    if stale_after_ms <= 0:
        raise ValueError("stale_after_ms must be positive")

    observation = PresenceObservation(
        presence_source=source,
        spatial_presence_source=_required_text(
            payload,
            "spatial_presence_source",
        ),
        zone=_required_text(payload, "zone"),
        timestamp=timestamp,
        fresh_until=timestamp + stale_after_ms / 1000.0,
        confidence=_bounded(packet["confidence"], "confidence"),
        range_confidence=_bounded(
            payload.get("range_confidence", 1.0),
            "range_confidence",
        ),
        living_motion_detected=bool(
            payload.get("living_motion_detected", False)
        ),
        identity_claim=payload.get("identity_claim"),
        owner_match_confidence=_bounded(
            payload.get("owner_match_confidence", 0.0),
            "owner_match_confidence",
        ),
        failure_mode=failure_mode,
        spoofing_risk=_bounded(
            payload.get("spoofing_risk", 0.0),
            "spoofing_risk",
        ),
        permitted_purposes=purposes,
    )
    return observation, simulated, _required_text(packet, "receipt_id")


def _required_text(document: Mapping[str, Any], key: str) -> str:
    value = document.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be non-empty" % key)
    return value.strip()


def _bounded(value: Any, name: str) -> float:
    number = float(value)
    if not 0.0 <= number <= 1.0:
        raise ValueError("%s must be between 0 and 1" % name)
    return number
