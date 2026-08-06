# SPDX-License-Identifier: GPL-3.0-only
"""Validated read-only context projected from a current cognitive workspace."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Tuple

_TERMINAL_STATES = {
    "COMPLETED",
    "INTERRUPTED",
    "STALE",
    "CONTRADICTED",
    "ABANDONED",
    "UNKNOWN_OUTCOME",
    "DEGRADED_COMPLETION",
}
_MODES = {"OBSERVE", "PROPOSE_ACTION", "TRACK_ACTION"}

_FORBIDDEN_AUTHORITY_KEYS = {
    "actuate",
    "actuation",
    "authorization",
    "authorized",
    "authorized_by",
    "capability",
    "capability_token",
    "command",
    "court_decision",
    "court_token",
    "execution_token",
    "executor",
    "executor_handle",
    "executor_name",
    "hardware_handle",
    "hardware_target",
    "permit",
    "policy_override",
    "retry_authorized",
    "safety_override",
    "shell",
    "token",
}
_AUTHORITY_CLAIM_KEYS = {
    "authority",
    "authority_granted",
    "grants_authority",
    "grants_execution",
    "grants_actuation",
    "execution_performed",
    "actuation_performed",
}


@dataclass(frozen=True)
class CognitiveWorkspaceContext:
    cognitive_event_id: str
    body_id: str
    node_id: str
    lifecycle_state: str
    mode: str
    source_refs: Tuple[str, ...]
    correlation_ids: Tuple[str, ...]
    proposal_refs: Tuple[str, ...]
    authorization_refs: Tuple[str, ...]
    execution_refs: Tuple[str, ...]
    prediction_refs: Tuple[str, ...]
    replay_state: str

    @classmethod
    def from_view(cls, view: Mapping[str, Any]) -> "CognitiveWorkspaceContext":
        if not isinstance(view, Mapping):
            raise ValueError("workspace view must be a mapping")
        required_flags = {
            "interpretation_only": True,
            "canonical_evidence": False,
            "authority": "none",
            "grants_authority": False,
            "grants_execution": False,
            "grants_actuation": False,
        }
        for key, expected in required_flags.items():
            if view.get(key) != expected:
                raise ValueError(
                    "workspace view %s must be %r" % (key, expected)
                )
        nested_check = {
            key: value
            for key, value in view.items()
            if key
            not in {
                "authority",
                "grants_authority",
                "grants_execution",
                "grants_actuation",
            }
        }
        forbidden = _find_named_keys(nested_check, _FORBIDDEN_AUTHORITY_KEYS)
        claims = _find_named_keys(nested_check, _AUTHORITY_CLAIM_KEYS)
        if forbidden or claims:
            raise ValueError(
                "workspace view contains forbidden authority fields: %s"
                % sorted(forbidden | claims)
            )
        for name in ("cognitive_event_id", "body_id", "node_id"):
            _require_text(name, view.get(name))
        lifecycle_state = view.get("lifecycle_state")
        if lifecycle_state in _TERMINAL_STATES:
            raise ValueError("workspace context is closed")
        if lifecycle_state not in {
            "OPEN",
            "DEVELOPING",
            "PROPOSAL_PENDING",
            "ACTION_TRACKING",
        }:
            raise ValueError("invalid workspace lifecycle_state")
        mode = view.get("mode")
        if mode not in _MODES:
            raise ValueError("invalid workspace mode")
        replay_state = view.get("replay_state")
        if replay_state not in {"live", "fixture", "replay"}:
            raise ValueError("invalid workspace replay_state")
        return cls(
            cognitive_event_id=view["cognitive_event_id"].strip(),
            body_id=view["body_id"].strip(),
            node_id=view["node_id"].strip(),
            lifecycle_state=lifecycle_state,
            mode=mode,
            source_refs=_text_sequence("source_refs", view.get("source_refs"), True),
            correlation_ids=_text_sequence(
                "correlation_ids", view.get("correlation_ids", ())
            ),
            proposal_refs=_text_sequence(
                "proposal_refs", view.get("proposal_refs", ())
            ),
            authorization_refs=_text_sequence(
                "authorization_refs", view.get("authorization_refs", ())
            ),
            execution_refs=_text_sequence(
                "execution_refs", view.get("execution_refs", ())
            ),
            prediction_refs=_text_sequence(
                "prediction_refs", view.get("prediction_refs", ())
            ),
            replay_state=replay_state,
        )

    @property
    def canonical(self) -> bool:
        return False

    @property
    def authority_granted(self) -> bool:
        return False

    def assert_matches(self, *, body_id: str, node_id: str) -> None:
        _require_text("body_id", body_id)
        _require_text("node_id", node_id)
        if self.body_id != body_id.strip():
            raise ValueError("workspace context belongs to another body")
        if self.node_id != node_id.strip():
            raise ValueError("workspace context belongs to another node")


def _find_named_keys(value: Any, names: set) -> set:
    found = set()
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if isinstance(key, str) and key.lower() in names:
                found.add(key.lower())
            found.update(_find_named_keys(nested, names))
    elif isinstance(value, (list, tuple, set)):
        for nested in value:
            found.update(_find_named_keys(nested, names))
    return found


def _text_sequence(name: str, values: Any, required: bool = False) -> Tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise ValueError("%s must be a list or tuple" % name)
    normalized = []
    for value in values:
        _require_text(name, value)
        stripped = value.strip()
        if stripped not in normalized:
            normalized.append(stripped)
    if required and not normalized:
        raise ValueError("%s must not be empty" % name)
    return tuple(normalized)


def _require_text(name: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % name)


__all__ = ["CognitiveWorkspaceContext"]
