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
    def judgment(self, ready=True, confidence=0.82):
        return JudgmentAssessment(
            confidence=confidence if ready else 0.3,
            band=ConfidenceBand.SUPPORTED if ready else ConfidenceBand.TENTATIVE,
            disposition=JudgmentDisposition.READY if ready else JudgmentDisposition.OBSERVE,
            reasons=("evidence-calibrated",),
            claim="battery voltage may continue falling",
            presentation_candidate=ready,
        )

    def expectation(self, active=True, confidence=0.86):
        if not active:
            return ExpectationAssessment(
                state=ExpectationState.NONE,
                disposition=ExpectationDisposition.OBSERVE,
                reasons=("no-active-expectation",),
            )
        candidate = ExpectationCandidate(
            statement="voltage may fall again while parked load remains active",
            pattern_statement="voltage repeatedly falls under parked accessory load",
            observation_key="vehicle.voltage.parked-load",
            scope="current-vehicle",
            triggering_conditions=("parked", "accessory-load-active"),
            evidence_references=("receipt:voltage-pattern-1",),
            state=ExpectationState.ACTIVE,
            confidence=confidence,
            formed_at=100.0,
            review_at=150.0,
            expires_at=400.0,
            horizon_seconds=300.0,
            support_count=5,
            independent_contexts=3,
            corroborating_sources=2,
            contradiction_count=0,
            missed_occurrences=0,
        )
        return ExpectationAssessment(
            state=ExpectationState.ACTIVE,
            disposition=ExpectationDisposition.FORM_CANDIDATE,
            reasons=("state:active",),
            candidate=candidate,
            eligible_for_intent_review=True,
        )

    def context(self, **overrides):
        values = {
            "proposed_statement": "consider reducing parked accessory load",
            "intent_kind": IntentKind.SUGGEST,
            "objective": "protect battery reserve",
            "evidence_references": ("receipt:voltage-pattern-1",),
            "constraints": ("owner-review-required",),
            "evaluated_at": 200.0,
            "expires_after_seconds": 180.0,
        }
        values.update(overrides)
        return IntentContext(**values)

    def test_supported_judgment_forms_reviewable_candidate(self):
        result = IntentEngine().assess(
            self.judgment(), self.expectation(active=False), self.context()
        )
        self.assertIs(result.state, IntentState.READY_FOR_REVIEW)
        self.assertTrue(result.eligible_for_downstream_review)
        self.assertIs(result.disposition, IntentDisposition.FORM_CANDIDATE)
        self.assertFalse(result.candidate.command)
        self.assertFalse(result.candidate.execution_authorized)
        self.assertEqual(result.candidate.authority, "none")

    def test_active_expectation_can_support_intent(self):
        result = IntentEngine().assess(
            self.judgment(ready=False), self.expectation(), self.context()
        )
        self.assertIs(result.state, IntentState.READY_FOR_REVIEW)
        self.assertIn("active-expectation", result.reasons)

    def test_weak_upstream_evidence_only_observes(self):
        result = IntentEngine().assess(
            self.judgment(ready=False), self.expectation(active=False), self.context()
        )
        self.assertIs(result.state, IntentState.NONE)
        self.assertIsNone(result.candidate)

    def test_missing_evidence_reference_blocks_candidate_formation(self):
        result = IntentEngine().assess(
            self.judgment(), self.expectation(active=False), self.context(evidence_references=())
        )
        self.assertIs(result.state, IntentState.NONE)
        self.assertIn("no-evidence", result.reasons[0])

    def test_contradiction_defers_then_withdraws(self):
        deferred = IntentEngine().assess(
            self.judgment(), self.expectation(), self.context(contradiction_count=1)
        )
        withdrawn = IntentEngine().assess(
            self.judgment(), self.expectation(), self.context(contradiction_count=2)
        )
        self.assertIs(deferred.state, IntentState.DEFERRED)
        self.assertIs(withdrawn.state, IntentState.WITHDRAWN)
        self.assertFalse(deferred.eligible_for_downstream_review)

    def test_existing_candidate_expires_without_automatic_renewal(self):
        result = IntentEngine().assess(
            self.judgment(),
            self.expectation(),
            self.context(
                evaluated_at=401.0,
                existing_candidate=True,
                existing_formed_at=200.0,
                existing_expires_at=400.0,
            ),
        )
        self.assertIs(result.state, IntentState.EXPIRED)
        self.assertEqual(result.candidate.formed_at, 200.0)
        self.assertEqual(result.candidate.expires_at, 400.0)

    def test_work_proposal_requires_runtime_review(self):
        result = IntentEngine().assess(
            self.judgment(),
            self.expectation(),
            self.context(intent_kind=IntentKind.PROPOSE_WORK),
        )
        self.assertTrue(result.candidate.requires_runtime_placement)
        self.assertFalse(result.candidate.runtime_placement_authorized)
        self.assertIn("runtime-placement-still-required", result.reasons)

    def test_consequential_proposal_requires_court_review(self):
        result = IntentEngine().assess(
            self.judgment(), self.expectation(), self.context(consequential=True)
        )
        self.assertTrue(result.candidate.requires_court_review)
        self.assertFalse(result.candidate.court_authorized)
        self.assertIn("court-review-still-required", result.reasons)

    def test_speech_shape_still_requires_presence(self):
        result = IntentEngine().assess(
            self.judgment(),
            self.expectation(),
            self.context(intent_kind=IntentKind.ASK, presence_allows_speech=False),
        )
        self.assertTrue(result.candidate.requires_presence_review)
        self.assertFalse(result.candidate.speaking_authorized)
        self.assertIn("presence-review-still-required", result.reasons)

    def test_integrity_and_safety_fail_closed(self):
        integrity = IntentEngine().assess(
            self.judgment(), self.expectation(), self.context(integrity_aligned=False)
        )
        safety = IntentEngine().assess(
            self.judgment(), self.expectation(), self.context(safety_priority=True)
        )
        self.assertIs(integrity.state, IntentState.BLOCKED)
        self.assertIs(safety.disposition, IntentDisposition.DEFER_TO_SAFETY)

    def test_identical_inputs_are_deterministic(self):
        engine = IntentEngine()
        judgment = self.judgment()
        expectation = self.expectation()
        context = self.context(intent_kind=IntentKind.PROPOSE_WORK)
        self.assertEqual(
            engine.assess(judgment, expectation, context),
            engine.assess(judgment, expectation, context),
        )


if __name__ == "__main__":
    unittest.main()
