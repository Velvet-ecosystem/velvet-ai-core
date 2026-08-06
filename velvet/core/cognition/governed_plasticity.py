# SPDX-License-Identifier: GPL-3.0-only
"""Policy contracts for future bounded cognitive adaptation.

This module does not learn, modify weights, write configuration, apply a change,
or grant authority. It only evaluates whether a proposed change has enough
bounded evidence to be observed, rejected, or forwarded to an external
promotion path.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from types import MappingProxyType
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Tuple
from uuid import uuid4


class PlasticityPosture(str, Enum):
    DISABLED = "disabled"
    OBSERVE_ONLY = "observe_only"
    PROPOSED = "proposed"
    APPROVED = "approved"


class PlasticityDisposition(str, Enum):
    REJECTED = "rejected"
    OBSERVED_ONLY = "observed_only"
    EXTERNAL_APPROVAL_REQUIRED = "external_approval_required"
    ELIGIBLE_FOR_EXTERNAL_PROMOTION = "eligible_for_external_promotion"


_PROTECTED_TOKENS = {
    "actuation",
    "actuator",
    "authentication",
    "authority",
    "brake",
    "can_write",
    "capability",
    "continuity",
    "court",
    "emergency",
    "executor",
    "identity",
    "medical",
    "policy",
    "receipt",
    "riven",
    "safety",
    "shell",
    "steering",
    "throttle",
}
_FORBIDDEN_PAYLOAD_KEYS = {
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


@dataclass(frozen=True)
class LearningComponentContract:
    component_id: str
    learning_domain: str
    mutable_fields: Tuple[str, ...]
    posture: PlasticityPosture = PlasticityPosture.DISABLED
    maximum_change: float = 0.0
    evidence_threshold: int = 1
    minimum_samples: int = 1
    validation_method: str = "deterministic-replay"
    rollback_checkpoint: str = "disabled-baseline"
    owner_presence_required: bool = True
    promotion_required: bool = True
    receipt_policy: str = "plasticity.promotion.v1"

    def __post_init__(self) -> None:
        _text("component_id", self.component_id)
        _text("learning_domain", self.learning_domain)
        _text_tuple("mutable_fields", self.mutable_fields, required=True)
        if not isinstance(self.posture, PlasticityPosture):
            raise ValueError("posture must be PlasticityPosture")
        _ratio("maximum_change", self.maximum_change)
        _positive_int("evidence_threshold", self.evidence_threshold)
        _positive_int("minimum_samples", self.minimum_samples)
        _text("validation_method", self.validation_method)
        _text("rollback_checkpoint", self.rollback_checkpoint)
        _text("receipt_policy", self.receipt_policy)
        for name, value in (
            ("owner_presence_required", self.owner_presence_required),
            ("promotion_required", self.promotion_required),
        ):
            if not isinstance(value, bool):
                raise ValueError("%s must be boolean" % name)
        protected = _protected_tokens((self.learning_domain,) + self.mutable_fields)
        if protected:
            raise ValueError(
                "learning contract touches protected domains: %s"
                % sorted(protected)
            )
        if self.posture is not PlasticityPosture.DISABLED:
            if self.maximum_change <= 0.0:
                raise ValueError("enabled plasticity requires maximum_change")
            if self.promotion_required is not True:
                raise ValueError("plasticity promotion must remain externally required")


@dataclass(frozen=True)
class LearningEvidence:
    evidence_id: str
    component_id: str
    body_id: str
    node_id: str
    source: str
    metric_name: str
    sample_count: int
    confidence: float
    source_refs: Tuple[str, ...]
    receipt_refs: Tuple[str, ...] = ()
    simulated: bool = False
    replay_state: str = "live"

    def __post_init__(self) -> None:
        for name, value in (
            ("evidence_id", self.evidence_id),
            ("component_id", self.component_id),
            ("body_id", self.body_id),
            ("node_id", self.node_id),
            ("source", self.source),
            ("metric_name", self.metric_name),
        ):
            _text(name, value)
        _positive_int("sample_count", self.sample_count)
        _ratio("confidence", self.confidence)
        _text_tuple("source_refs", self.source_refs, required=True)
        _text_tuple("receipt_refs", self.receipt_refs)
        if not isinstance(self.simulated, bool):
            raise ValueError("simulated must be boolean")
        if self.replay_state not in {"live", "fixture", "replay"}:
            raise ValueError("invalid replay_state")
        protected = _protected_tokens((self.metric_name,))
        if protected:
            raise ValueError(
                "learning evidence targets protected domains: %s"
                % sorted(protected)
            )


@dataclass(frozen=True)
class ChangeDelta:
    field_name: str
    before: Any
    after: Any
    normalized_magnitude: float

    def __post_init__(self) -> None:
        _text("field_name", self.field_name)
        _ratio("normalized_magnitude", self.normalized_magnitude)
        protected = _protected_tokens((self.field_name,))
        if protected:
            raise ValueError(
                "change delta touches protected domains: %s"
                % sorted(protected)
            )
        _reject_forbidden(self.before, "before")
        _reject_forbidden(self.after, "after")
        if self.before == self.after and self.normalized_magnitude != 0.0:
            raise ValueError("unchanged value must have zero magnitude")
        if self.before != self.after and self.normalized_magnitude <= 0.0:
            raise ValueError("changed value requires positive magnitude")


@dataclass(frozen=True)
class PlasticityProposal:
    proposal_id: str
    component_id: str
    body_id: str
    node_id: str
    deltas: Tuple[ChangeDelta, ...]
    evidence: Tuple[LearningEvidence, ...]
    checkpoint_ref: str
    validation_ref: str
    source_refs: Tuple[str, ...]
    created_at: float
    expires_at: float
    replay_state: str = "live"
    owner_presence_ref: Optional[str] = None
    owner_presence_verified_by: Optional[str] = None
    owner_presence_simulated: bool = False
    approval_ref: Optional[str] = None
    promotion_receipt_ref: Optional[str] = None

    def __post_init__(self) -> None:
        for name, value in (
            ("proposal_id", self.proposal_id),
            ("component_id", self.component_id),
            ("body_id", self.body_id),
            ("node_id", self.node_id),
            ("checkpoint_ref", self.checkpoint_ref),
            ("validation_ref", self.validation_ref),
        ):
            _text(name, value)
        if not isinstance(self.deltas, tuple) or not self.deltas:
            raise ValueError("deltas must be a non-empty tuple")
        if not all(isinstance(item, ChangeDelta) for item in self.deltas):
            raise ValueError("deltas must contain ChangeDelta values")
        fields = [item.field_name for item in self.deltas]
        if len(fields) != len(set(fields)):
            raise ValueError("proposal cannot repeat a mutable field")
        if not isinstance(self.evidence, tuple) or not all(
            isinstance(item, LearningEvidence) for item in self.evidence
        ):
            raise ValueError("evidence must be a tuple of LearningEvidence")
        ids = [item.evidence_id for item in self.evidence]
        if len(ids) != len(set(ids)):
            raise ValueError("proposal evidence IDs must be unique")
        _text_tuple("source_refs", self.source_refs, required=True)
        _non_negative("created_at", self.created_at)
        _non_negative("expires_at", self.expires_at)
        if float(self.expires_at) <= float(self.created_at):
            raise ValueError("expires_at must follow created_at")
        if self.replay_state not in {"live", "fixture", "replay"}:
            raise ValueError("invalid replay_state")
        if not isinstance(self.owner_presence_simulated, bool):
            raise ValueError("owner_presence_simulated must be boolean")
        for name, value in (
            ("owner_presence_ref", self.owner_presence_ref),
            ("owner_presence_verified_by", self.owner_presence_verified_by),
            ("approval_ref", self.approval_ref),
            ("promotion_receipt_ref", self.promotion_receipt_ref),
        ):
            if value is not None:
                _text(name, value)

    @property
    def maximum_magnitude(self) -> float:
        return max(item.normalized_magnitude for item in self.deltas)

    def fingerprint(self) -> str:
        document = {
            "proposal_id": self.proposal_id,
            "component_id": self.component_id,
            "body_id": self.body_id,
            "node_id": self.node_id,
            "deltas": [
                {
                    "field_name": item.field_name,
                    "before": item.before,
                    "after": item.after,
                    "normalized_magnitude": item.normalized_magnitude,
                }
                for item in self.deltas
            ],
            "evidence_ids": [item.evidence_id for item in self.evidence],
            "checkpoint_ref": self.checkpoint_ref,
            "validation_ref": self.validation_ref,
            "source_refs": list(self.source_refs),
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "replay_state": self.replay_state,
            "owner_presence_ref": self.owner_presence_ref,
            "owner_presence_verified_by": self.owner_presence_verified_by,
            "owner_presence_simulated": self.owner_presence_simulated,
            "approval_ref": self.approval_ref,
            "promotion_receipt_ref": self.promotion_receipt_ref,
        }
        encoded = json.dumps(
            document,
            sort_keys=True,
            separators=(",", ":"),
            default=repr,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class PlasticityDecision:
    decision_id: str
    proposal_id: str
    component_id: str
    disposition: PlasticityDisposition
    reasons: Tuple[str, ...]
    evidence_refs: Tuple[str, ...]
    source_refs: Tuple[str, ...]
    rollback_checkpoint: str
    validation_ref: str
    proposal_fingerprint: str
    promotion_eligible: bool = False
    requires_external_promotion: bool = True
    change_applied: bool = False
    authority_granted: bool = False

    def __post_init__(self) -> None:
        for name, value in (
            ("decision_id", self.decision_id),
            ("proposal_id", self.proposal_id),
            ("component_id", self.component_id),
            ("rollback_checkpoint", self.rollback_checkpoint),
            ("validation_ref", self.validation_ref),
            ("proposal_fingerprint", self.proposal_fingerprint),
        ):
            _text(name, value)
        if not isinstance(self.disposition, PlasticityDisposition):
            raise ValueError("disposition must be PlasticityDisposition")
        _text_tuple("reasons", self.reasons, required=True)
        _text_tuple("evidence_refs", self.evidence_refs)
        _text_tuple("source_refs", self.source_refs, required=True)
        if self.change_applied is not False:
            raise ValueError("AI Core plasticity decision cannot apply changes")
        if self.authority_granted is not False:
            raise ValueError("plasticity decision cannot grant authority")
        if self.requires_external_promotion is not True:
            raise ValueError("external promotion must remain required")
        expected = (
            self.disposition
            is PlasticityDisposition.ELIGIBLE_FOR_EXTERNAL_PROMOTION
        )
        if self.promotion_eligible is not expected:
            raise ValueError("promotion_eligible does not match disposition")

    def read_only_view(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "decision_id": self.decision_id,
                "proposal_id": self.proposal_id,
                "component_id": self.component_id,
                "disposition": self.disposition.value,
                "reasons": self.reasons,
                "evidence_refs": self.evidence_refs,
                "source_refs": self.source_refs,
                "rollback_checkpoint": self.rollback_checkpoint,
                "validation_ref": self.validation_ref,
                "proposal_fingerprint": self.proposal_fingerprint,
                "promotion_eligible": self.promotion_eligible,
                "requires_external_promotion": True,
                "change_applied": False,
                "authority_granted": False,
            }
        )


class GovernedPlasticityRegistry:
    """Evaluate adaptation proposals without applying them."""

    def __init__(
        self,
        *,
        body_id: str,
        node_id: str,
        replay_state: str = "live",
        id_factory: Optional[Callable[[str], str]] = None,
    ) -> None:
        _text("body_id", body_id)
        _text("node_id", node_id)
        if replay_state not in {"live", "fixture", "replay"}:
            raise ValueError("invalid replay_state")
        self.body_id = body_id.strip()
        self.node_id = node_id.strip()
        self.replay_state = replay_state
        self._id = id_factory or (lambda p: "%s_%s" % (p, uuid4().hex))
        self._contracts: Dict[str, LearningComponentContract] = {}
        self._decisions: Dict[str, PlasticityDecision] = {}
        self._fingerprints: Dict[str, str] = {}

    def register(self, contract: LearningComponentContract) -> None:
        if not isinstance(contract, LearningComponentContract):
            raise ValueError("contract must be LearningComponentContract")
        if contract.component_id in self._contracts:
            raise ValueError("component contract already registered")
        self._contracts[contract.component_id] = contract

    def evaluate(
        self,
        proposal: PlasticityProposal,
        *,
        now: float,
    ) -> PlasticityDecision:
        if not isinstance(proposal, PlasticityProposal):
            raise ValueError("proposal must be PlasticityProposal")
        _non_negative("now", now)
        fingerprint = proposal.fingerprint()
        if proposal.proposal_id in self._decisions:
            if self._fingerprints[proposal.proposal_id] != fingerprint:
                raise ValueError("proposal ID was reused with different content")
            return self._decisions[proposal.proposal_id]
        if proposal.component_id not in self._contracts:
            return self._record(
                proposal,
                PlasticityDisposition.REJECTED,
                ("component has no registered learning contract",),
                fingerprint,
            )
        contract = self._contracts[proposal.component_id]
        reasons = []

        if proposal.body_id != self.body_id:
            reasons.append("proposal belongs to another body")
        if proposal.node_id != self.node_id:
            reasons.append("proposal belongs to another node")
        if proposal.replay_state != self.replay_state:
            reasons.append("proposal replay_state differs from registry")
        if float(now) > float(proposal.expires_at):
            reasons.append("proposal expired")
        if proposal.checkpoint_ref != contract.rollback_checkpoint:
            reasons.append("rollback checkpoint does not match contract")
        if proposal.maximum_magnitude > contract.maximum_change:
            reasons.append("proposed change exceeds maximum_change")

        proposed_fields = {item.field_name for item in proposal.deltas}
        unknown_fields = proposed_fields - set(contract.mutable_fields)
        if unknown_fields:
            reasons.append(
                "proposal contains non-mutable fields: %s"
                % sorted(unknown_fields)
            )

        evidence_refs = []
        total_samples = 0
        real_evidence = True
        for item in proposal.evidence:
            evidence_refs.append(item.evidence_id)
            if item.component_id != contract.component_id:
                reasons.append("evidence belongs to another component")
            if item.body_id != self.body_id:
                reasons.append("evidence belongs to another body")
            if item.node_id != self.node_id:
                reasons.append("evidence belongs to another node")
            if item.replay_state != proposal.replay_state:
                reasons.append("evidence replay_state differs from proposal")
            total_samples += item.sample_count
            if item.simulated or item.replay_state != "live":
                real_evidence = False
        if len(proposal.evidence) < contract.evidence_threshold:
            reasons.append("insufficient evidence records")
        if total_samples < contract.minimum_samples:
            reasons.append("insufficient evidence samples")

        if contract.posture is PlasticityPosture.DISABLED:
            reasons.append("component plasticity is disabled")
            return self._record(
                proposal,
                PlasticityDisposition.REJECTED,
                tuple(reasons),
                fingerprint,
                evidence_refs=tuple(evidence_refs),
            )

        if reasons:
            return self._record(
                proposal,
                PlasticityDisposition.REJECTED,
                tuple(reasons),
                fingerprint,
                evidence_refs=tuple(evidence_refs),
            )

        if contract.posture is PlasticityPosture.OBSERVE_ONLY:
            return self._record(
                proposal,
                PlasticityDisposition.OBSERVED_ONLY,
                ("component is restricted to observe-only adaptation",),
                fingerprint,
                evidence_refs=tuple(evidence_refs),
            )

        approval_reasons = []
        if self.replay_state != "live" or not real_evidence:
            approval_reasons.append(
                "fixture, replay, or simulated evidence cannot be promoted"
            )
        if contract.owner_presence_required:
            if proposal.owner_presence_ref is None:
                approval_reasons.append("verified owner presence is required")
            if proposal.owner_presence_verified_by != "velvet-runtime":
                approval_reasons.append(
                    "owner presence must be verified by velvet-runtime"
                )
            if proposal.owner_presence_simulated:
                approval_reasons.append("simulated owner presence cannot approve")
        if contract.promotion_required and proposal.approval_ref is None:
            approval_reasons.append("external approval reference is required")
        if proposal.promotion_receipt_ref is None:
            approval_reasons.append("promotion receipt reference is required")

        if contract.posture is PlasticityPosture.PROPOSED:
            if not approval_reasons:
                approval_reasons.append(
                    "component posture remains proposed, not approved"
                )
            return self._record(
                proposal,
                PlasticityDisposition.EXTERNAL_APPROVAL_REQUIRED,
                tuple(approval_reasons),
                fingerprint,
                evidence_refs=tuple(evidence_refs),
            )

        if approval_reasons:
            return self._record(
                proposal,
                PlasticityDisposition.EXTERNAL_APPROVAL_REQUIRED,
                tuple(approval_reasons),
                fingerprint,
                evidence_refs=tuple(evidence_refs),
            )

        return self._record(
            proposal,
            PlasticityDisposition.ELIGIBLE_FOR_EXTERNAL_PROMOTION,
            (
                "bounded evidence and external promotion references are present",
                "AI Core has not applied the proposed change",
            ),
            fingerprint,
            evidence_refs=tuple(evidence_refs),
        )

    def decision(self, proposal_id: str) -> PlasticityDecision:
        _text("proposal_id", proposal_id)
        if proposal_id not in self._decisions:
            raise KeyError("unknown proposal_id")
        return self._decisions[proposal_id]

    def contract(self, component_id: str) -> LearningComponentContract:
        _text("component_id", component_id)
        if component_id not in self._contracts:
            raise KeyError("unknown component_id")
        return self._contracts[component_id]

    def _record(
        self,
        proposal: PlasticityProposal,
        disposition: PlasticityDisposition,
        reasons: Tuple[str, ...],
        fingerprint: str,
        *,
        evidence_refs: Tuple[str, ...] = (),
    ) -> PlasticityDecision:
        source_refs = _merge(
            proposal.source_refs,
            evidence_refs,
            (proposal.checkpoint_ref, proposal.validation_ref),
            _optional_tuple(proposal.owner_presence_ref),
            _optional_tuple(proposal.approval_ref),
            _optional_tuple(proposal.promotion_receipt_ref),
        )
        decision = PlasticityDecision(
            decision_id=self._id("plasticity-decision"),
            proposal_id=proposal.proposal_id,
            component_id=proposal.component_id,
            disposition=disposition,
            reasons=reasons,
            evidence_refs=evidence_refs,
            source_refs=source_refs,
            rollback_checkpoint=proposal.checkpoint_ref,
            validation_ref=proposal.validation_ref,
            proposal_fingerprint=fingerprint,
            promotion_eligible=(
                disposition
                is PlasticityDisposition.ELIGIBLE_FOR_EXTERNAL_PROMOTION
            ),
        )
        self._decisions[proposal.proposal_id] = decision
        self._fingerprints[proposal.proposal_id] = fingerprint
        return decision


def _protected_tokens(values: Iterable[str]) -> set:
    found = set()
    for value in values:
        lowered = value.lower().replace("-", "_").replace(".", "_")
        parts = set(filter(None, lowered.split("_")))
        for token in _PROTECTED_TOKENS:
            if token in parts or token in lowered:
                found.add(token)
    return found


def _reject_forbidden(value: Any, name: str) -> None:
    found = _find_forbidden(value)
    if found:
        raise ValueError(
            "%s contains forbidden authority fields: %s"
            % (name, sorted(found))
        )


def _find_forbidden(value: Any) -> set:
    found = set()
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if isinstance(key, str) and key.lower() in _FORBIDDEN_PAYLOAD_KEYS:
                found.add(key.lower())
            found.update(_find_forbidden(nested))
    elif isinstance(value, (list, tuple, set)):
        for nested in value:
            found.update(_find_forbidden(nested))
    return found


def _merge(*groups: Iterable[str]) -> Tuple[str, ...]:
    result = []
    for group in groups:
        for value in group:
            if value not in result:
                result.append(value)
    return tuple(result)


def _optional_tuple(value: Optional[str]) -> Tuple[str, ...]:
    return () if value is None else (value,)


def _text(name: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % name)


def _text_tuple(name: str, values: Any, required: bool = False) -> None:
    if not isinstance(values, tuple):
        raise ValueError("%s must be a tuple" % name)
    if required and not values:
        raise ValueError("%s must not be empty" % name)
    for value in values:
        _text(name, value)


def _ratio(name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s must be numeric" % name)
    if not 0.0 <= float(value) <= 1.0:
        raise ValueError("%s must be between 0 and 1" % name)


def _positive_int(name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("%s must be a positive integer" % name)


def _non_negative(name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("%s must be numeric" % name)
    if float(value) < 0.0:
        raise ValueError("%s must be non-negative" % name)


__all__ = [
    "PlasticityPosture",
    "PlasticityDisposition",
    "LearningComponentContract",
    "LearningEvidence",
    "ChangeDelta",
    "PlasticityProposal",
    "PlasticityDecision",
    "GovernedPlasticityRegistry",
]
