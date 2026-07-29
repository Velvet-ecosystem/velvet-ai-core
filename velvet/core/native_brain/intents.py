# SPDX-License-Identifier: GPL-3.0-only
"""Deterministic, proposal-only intent formation for Native Brain.

Intent formation describes what Velvet may wish to do next. It never speaks,
writes memory, selects a node, creates a Runtime lease, authorizes Court,
executes tools, touches hardware, or performs actuation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from .expectations import (
    ExpectationAssessment,
    ExpectationDisposition,
    ExpectationState,
)
from .judgment import JudgmentAssessment, JudgmentDisposition


class IntentKind(str, Enum):
    WATCH = "watch"
    ASK = "ask"
    SUGGEST = "suggest"
    REQUEST_AUTHORIZED_ACTION = "request_authorized_action"


class IntentState(str, Enum):
    NONE = "none"
    CANDIDATE = "candidate"
    READY_FOR_REVIEW = "ready_for_review"
    DEFERRED = "deferred"
    RETIRED = "retired"
    BLOCKED = "blocked"


class IntentDisposition(str, Enum):
    BLOCKED = "blocked"
    DEFER_TO_SAFETY = "defer_to_safety"
    OBSERVE = "observe"
    FORM_CANDIDATE = "form_candidate"
    RETAIN_CANDIDATE = "retain_candidate"
    DEFER_CANDIDATE = "defer_candidate"
    RETIRE_CANDIDATE = "retire_candidate"


@dataclass(frozen=True)
class IntentContext:
    """Domain framing for one proposal-only intent review."""

    kind: Optional[IntentKind] = None
    statement: Optional[str] = None
    rationale: Optional[str] = None
    evidence_references: Tuple[str, ...] = ()
    required_capabilities: Tuple[str, ...] = ()
    consequential: bool = False
    user_present: bool = False
    interruption_allowed: bool = False
    existing_candidate: bool = False
    superseded: bool = False
    integrity_aligned: bool = True
    continuity_verified: bool = True
    runtime_context_verified: bool = True
    safety_priority: bool = False

    def __post_init__(self) -> None:
        for name, value in (("statement", self.statement), ("rationale", self.rationale)):
            if value is not None and not value.strip():
                raise ValueError(f"{name} cannot be blank")
        _validate_text_tuple(self.evidence_references, "evidence_references")
        _validate_text_tuple(self.required_capabilities, "required_capabilities")
        if self.kind is not None and (self.statement is None or self.rationale is None):
            raise ValueError("intent kind requires statement and rationale")
        if self.kind is IntentKind.REQUEST_AUTHORIZED_ACTION and not self.consequential:
            raise ValueError("authorized-action requests must be marked consequential")
        if self.kind is not IntentKind.REQUEST_AUTHORIZED_ACTION and self.consequential:
            raise ValueError("consequential intents must request authorized action")


@dataclass(frozen=True)
class IntentCandidate:
    kind: IntentKind
    statement: str
    rationale: str
    evidence_references: Tuple[str, ...]
    required_capabilities: Tuple[str, ...]
    state: IntentState
    consequential: bool
    requires_presence: bool
    requires_runtime_placement: bool
    requires_court_authorization: bool
    candidate: bool = True
    proposal_only: bool = True
    canonical: bool = False
    speaking_authorized: bool = False
    interruption_authorized: bool = False
    memory_write_authorized: bool = False
    runtime_placement_authorized: bool = False
    court_authorized: bool = False
    execution_authorized: bool = False
    actuation_authorized: bool = False
    authority: str = "none"

    def __post_init__(self) -> None:
        if not self.statement.strip() or not self.rationale.strip():
            raise ValueError("intent statement and rationale are required")
        _validate_text_tuple(self.evidence_references, "evidence_references")
        _validate_text_tuple(self.required_capabilities, "required_capabilities")
        if not self.evidence_references:
            raise ValueError("intent candidates require evidence references")
        if self.state not in {
            IntentState.CANDIDATE,
            IntentState.READY_FOR_REVIEW,
            IntentState.DEFERRED,
            IntentState.RETIRED,
        }:
            raise ValueError("intent candidates require a candidate state")
        if not self.candidate or not self.proposal_only:
            raise ValueError("intent objects must remain proposal-only candidates")
        if self.canonical:
            raise ValueError("intent candidates cannot be canonical")
        if any((
            self.speaking_authorized,
            self.interruption_authorized,
            self.memory_write_authorized,
            self.runtime_placement_authorized,
            self.court_authorized,
            self.execution_authorized,
            self.actuation_authorized,
        )):
            raise ValueError("intent candidates cannot authorize downstream effects")
        if self.authority != "none":
            raise ValueError("intent candidates cannot carry authority")
        if self.consequential != self.requires_court_authorization:
            raise ValueError("consequential intent must independently require Court")
        if self.kind is IntentKind.REQUEST_AUTHORIZED_ACTION:
            if not self.requires_runtime_placement or not self.requires_court_authorization:
                raise ValueError("authorized-action requests require Runtime and Court review")
        elif self.requires_runtime_placement or self.requires_court_authorization:
            raise ValueError("non-action intents cannot claim Runtime or Court requirements")


@dataclass(frozen=True)
class IntentAssessment:
    state: IntentState
    disposition: IntentDisposition
    reasons: Tuple[str, ...]
    candidate: Optional[IntentCandidate] = None
    eligible_for_presence_review: bool = False
    eligible_for_runtime_review: bool = False
    canonical: bool = False
    authority: str = "none"

    def __post_init__(self) -> None:
        if not self.reasons:
            raise ValueError("intent assessment reasons are required")
        candidate_dispositions = {
            IntentDisposition.FORM_CANDIDATE,
            IntentDisposition.RETAIN_CANDIDATE,
            IntentDisposition.DEFER_CANDIDATE,
            IntentDisposition.RETIRE_CANDIDATE,
        }
        if self.disposition in candidate_dispositions and self.candidate is None:
            raise ValueError("candidate dispositions require an intent candidate")
        if self.candidate is not None and self.candidate.state is not self.state:
            raise ValueError("assessment and candidate intent states must match")
        if self.eligible_for_presence_review:
            if self.state is not IntentState.READY_FOR_REVIEW or self.candidate is None:
                raise ValueError("presence review requires a ready candidate")
        if self.eligible_for_runtime_review:
            if (
                self.state is not IntentState.READY_FOR_REVIEW
                or self.candidate is None
                or self.candidate.kind is not IntentKind.REQUEST_AUTHORIZED_ACTION
            ):
                raise ValueError("Runtime review requires a ready authorized-action request")
        if self.canonical or self.authority != "none":
            raise ValueError("intent assessments remain non-canonical and authority-free")


class IntentEngine:
    """Form bounded proposals without confusing desire with permission."""

    def assess(
        self,
        expectation: ExpectationAssessment,
        judgment: JudgmentAssessment,
        context: IntentContext,
    ) -> IntentAssessment:
        blocked = []
        if not context.integrity_aligned:
            blocked.append("integrity-not-aligned")
        if not context.continuity_verified:
            blocked.append("continuity-not-verified")
        if not context.runtime_context_verified:
            blocked.append("runtime-context-not-verified")
        if blocked:
            return IntentAssessment(IntentState.BLOCKED, IntentDisposition.BLOCKED, tuple(blocked))

        if (
            context.safety_priority
            or expectation.disposition is ExpectationDisposition.DEFER_TO_SAFETY
            or judgment.disposition is JudgmentDisposition.DEFER_TO_SAFETY
        ):
            return IntentAssessment(
                IntentState.BLOCKED,
                IntentDisposition.DEFER_TO_SAFETY,
                ("safety-path-owns-next-decision",),
            )

        if context.kind is None:
            return IntentAssessment(
                IntentState.NONE,
                IntentDisposition.OBSERVE,
                ("no-domain-intent-proposal",),
            )
        if not context.evidence_references:
            return IntentAssessment(
                IntentState.NONE,
                IntentDisposition.OBSERVE,
                ("no-evidence-references",),
            )
        if context.superseded:
            candidate = self._candidate(context, IntentState.RETIRED)
            return IntentAssessment(
                IntentState.RETIRED,
                IntentDisposition.RETIRE_CANDIDATE,
                ("intent-superseded",),
                candidate,
            )

        expectation_ready = (
            expectation.state is ExpectationState.ACTIVE
            and expectation.eligible_for_intent_review
            and expectation.candidate is not None
        )
        judgment_ready = (
            judgment.disposition is JudgmentDisposition.READY
            and judgment.claim is not None
        )
        if context.kind in {IntentKind.WATCH, IntentKind.ASK}:
            upstream_ready = expectation_ready or judgment_ready
        else:
            upstream_ready = expectation_ready and judgment_ready
        if not upstream_ready:
            return IntentAssessment(
                IntentState.NONE,
                IntentDisposition.OBSERVE,
                ("upstream-evidence-not-ready-for-intent",),
            )

        requires_presence = context.kind in {
            IntentKind.ASK,
            IntentKind.SUGGEST,
            IntentKind.REQUEST_AUTHORIZED_ACTION,
        }
        review_ready = not requires_presence or (
            context.user_present and context.interruption_allowed
        )
        state = IntentState.READY_FOR_REVIEW if review_ready else IntentState.DEFERRED
        disposition = (
            IntentDisposition.RETAIN_CANDIDATE
            if context.existing_candidate and review_ready
            else IntentDisposition.FORM_CANDIDATE
            if review_ready
            else IntentDisposition.DEFER_CANDIDATE
        )
        candidate = self._candidate(context, state)
        reasons = [f"kind:{context.kind.value}", f"state:{state.value}"]
        if requires_presence:
            reasons.append("presence-gated")
        if context.kind is IntentKind.REQUEST_AUTHORIZED_ACTION:
            reasons.extend(("runtime-placement-required", "court-authorization-required"))
        if state is IntentState.DEFERRED:
            reasons.append("wait-for-presence-window")

        return IntentAssessment(
            state=state,
            disposition=disposition,
            reasons=tuple(reasons),
            candidate=candidate,
            eligible_for_presence_review=state is IntentState.READY_FOR_REVIEW and requires_presence,
            eligible_for_runtime_review=(
                state is IntentState.READY_FOR_REVIEW
                and context.kind is IntentKind.REQUEST_AUTHORIZED_ACTION
            ),
        )

    @staticmethod
    def _candidate(context: IntentContext, state: IntentState) -> IntentCandidate:
        assert context.kind is not None
        assert context.statement is not None
        assert context.rationale is not None
        action_request = context.kind is IntentKind.REQUEST_AUTHORIZED_ACTION
        return IntentCandidate(
            kind=context.kind,
            statement=context.statement,
            rationale=context.rationale,
            evidence_references=context.evidence_references,
            required_capabilities=context.required_capabilities,
            state=state,
            consequential=context.consequential,
            requires_presence=context.kind is not IntentKind.WATCH,
            requires_runtime_placement=action_request,
            requires_court_authorization=action_request,
        )


def _validate_text_tuple(value: Tuple[str, ...], name: str) -> None:
    if not isinstance(value, tuple):
        raise ValueError(f"{name} must be a tuple")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{name} must contain non-empty strings")
