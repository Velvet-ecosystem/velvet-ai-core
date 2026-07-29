# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet.core.native_brain import (
    ConfidenceBand,
    ExpectationAssessment,
    ExpectationCandidate,
    ExpectationDisposition,
    ExpectationState,
    IntentContext,
    IntentDisposition,
    IntentEngine,
    IntentKind,
    IntentState,
    JudgmentAssessment,
    JudgmentDisposition,
)


class NativeBrainIntentTests(unittest.TestCase):
    def judgment(self, ready=True):
        return JudgmentAssessment(
            confidence=0.9 if ready else 0.2,
            band=ConfidenceBand.STRONG if ready else ConfidenceBand.INSUFFICIENT,
            disposition=JudgmentDisposition.READY if ready else JudgmentDisposition.OBSERVE,
            reasons=("evidence-calibrated",),
            claim="battery load is trending downward" if ready else None,
            presentation_candidate=ready,
        )

    def expectation(self, active=True):
        candidate = None
        if active:
            candidate = ExpectationCandidate(
                statement="battery may fall below threshold within 20 minutes",
                pattern_statement="battery falls during prolonged parked audio load",
                observation_key="vehicle.battery.parked-load",
                scope="current-vehicle",
                triggering_conditions=("parked", "audio-load-active"),
                evidence_references=("receipt-1", "receipt-2"),
                state=ExpectationState.ACTIVE,
                confidence=0.9,
                formed_at=100.0,
                review_at=160.0,
                expires_at=1300.0,
                horizon_seconds=1200.0,
                support_count=5,
                independent_contexts=3,
                corroborating_sources=2,
                contradiction_count=0,
                missed_occurrences=0,
            )
        return ExpectationAssessment(
            state=ExpectationState.ACTIVE if active else ExpectationState.NONE,
            disposition=ExpectationDisposition.RETAIN_CANDIDATE if active else ExpectationDisposition.OBSERVE,
            reasons=("state:active",) if active else ("stable-pattern-required",),
            candidate=candidate,
            eligible_for_intent_review=active,
        )

    def context(self, kind=IntentKind.WATCH, **overrides):
        values = {
            "kind": kind,
            "statement": "watch battery trend",
            "rationale": "active expectation warrants quiet observation",
            "evidence_references": ("receipt-1", "expectation-1"),
            "required_capabilities": ("battery-observation",),
            "user_present": True,
            "interruption_allowed": True,
        }
        if kind is IntentKind.REQUEST_AUTHORIZED_ACTION:
            values.update({
                "statement": "request reduction of non-critical audio load",
                "rationale": "protect battery reserve",
                "consequential": True,
                "required_capabilities": ("audio-load-control",),
            })
        values.update(overrides)
        return IntentContext(**values)

    def test_watch_intent_can_be_ready_without_presence(self):
        result = IntentEngine().assess(
            self.expectation(), self.judgment(),
            self.context(user_present=False, interruption_allowed=False),
        )
        self.assertIs(result.state, IntentState.READY_FOR_REVIEW)
        self.assertFalse(result.eligible_for_presence_review)
        self.assertFalse(result.eligible_for_runtime_review)

    def test_ask_waits_for_presence_window(self):
        result = IntentEngine().assess(
            self.expectation(), self.judgment(),
            self.context(IntentKind.ASK, user_present=False, interruption_allowed=False),
        )
        self.assertIs(result.state, IntentState.DEFERRED)
        self.assertIs(result.disposition, IntentDisposition.DEFER_CANDIDATE)
        self.assertFalse(result.candidate.speaking_authorized)
        self.assertFalse(result.candidate.interruption_authorized)

    def test_suggestion_requires_both_expectation_and_judgment(self):
        result = IntentEngine().assess(
            self.expectation(active=False), self.judgment(), self.context(IntentKind.SUGGEST),
        )
        self.assertIs(result.state, IntentState.NONE)
        self.assertIsNone(result.candidate)

    def test_authorized_action_request_requires_runtime_and_court_review(self):
        result = IntentEngine().assess(
            self.expectation(), self.judgment(),
            self.context(IntentKind.REQUEST_AUTHORIZED_ACTION),
        )
        self.assertIs(result.state, IntentState.READY_FOR_REVIEW)
        self.assertTrue(result.eligible_for_runtime_review)
        candidate = result.candidate
        self.assertTrue(candidate.requires_runtime_placement)
        self.assertTrue(candidate.requires_court_authorization)
        self.assertFalse(candidate.runtime_placement_authorized)
        self.assertFalse(candidate.court_authorized)
        self.assertFalse(candidate.execution_authorized)
        self.assertFalse(candidate.actuation_authorized)
        self.assertEqual(candidate.authority, "none")

    def test_missing_evidence_forms_no_intent(self):
        result = IntentEngine().assess(
            self.expectation(), self.judgment(),
            self.context(evidence_references=()),
        )
        self.assertIs(result.state, IntentState.NONE)
        self.assertIn("no-evidence", result.reasons[0])

    def test_safety_path_outranks_intent(self):
        result = IntentEngine().assess(
            self.expectation(), self.judgment(),
            self.context(safety_priority=True),
        )
        self.assertIs(result.state, IntentState.BLOCKED)
        self.assertIs(result.disposition, IntentDisposition.DEFER_TO_SAFETY)

    def test_integrity_failure_blocks_intent(self):
        result = IntentEngine().assess(
            self.expectation(), self.judgment(),
            self.context(integrity_aligned=False),
        )
        self.assertIs(result.state, IntentState.BLOCKED)
        self.assertEqual(result.authority, "none")

    def test_superseded_candidate_is_retired(self):
        result = IntentEngine().assess(
            self.expectation(), self.judgment(),
            self.context(existing_candidate=True, superseded=True),
        )
        self.assertIs(result.state, IntentState.RETIRED)
        self.assertIs(result.disposition, IntentDisposition.RETIRE_CANDIDATE)

    def test_consequential_non_action_intent_is_rejected(self):
        with self.assertRaises(ValueError):
            self.context(IntentKind.SUGGEST, consequential=True)

    def test_action_request_must_be_consequential(self):
        with self.assertRaises(ValueError):
            IntentContext(
                kind=IntentKind.REQUEST_AUTHORIZED_ACTION,
                statement="request action",
                rationale="reason",
                evidence_references=("r1",),
                consequential=False,
            )

    def test_candidate_cannot_claim_downstream_authority(self):
        result = IntentEngine().assess(
            self.expectation(), self.judgment(), self.context(IntentKind.ASK),
        )
        candidate = result.candidate
        self.assertFalse(candidate.canonical)
        self.assertFalse(candidate.speaking_authorized)
        self.assertFalse(candidate.memory_write_authorized)
        self.assertFalse(candidate.execution_authorized)

    def test_identical_inputs_are_deterministic(self):
        expectation = self.expectation()
        judgment = self.judgment()
        context = self.context(IntentKind.SUGGEST)
        engine = IntentEngine()
        self.assertEqual(
            engine.assess(expectation, judgment, context),
            engine.assess(expectation, judgment, context),
        )


if __name__ == "__main__":
    unittest.main()
