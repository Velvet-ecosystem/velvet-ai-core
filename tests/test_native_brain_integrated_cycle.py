# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet.core.native_brain.attention import AttentionContext
from velvet.core.native_brain.cognition import ObservationEnvelope
from velvet.core.native_brain.curiosity import CuriosityContext, CuriosityDisposition
from velvet.core.native_brain.expectations import ExpectationContext, ExpectationState
from velvet.core.native_brain.integrated_cycle import (
    IntegratedCognitiveCycle,
    IntegratedCycleContext,
    IntegratedCycleOutcome,
    IntegratedCycleStage,
)
from velvet.core.native_brain.intents import IntentContext, IntentKind, IntentState
from velvet.core.native_brain.judgment import JudgmentContext, JudgmentDisposition
from velvet.core.native_brain.patterns import PatternContext, PatternState
from velvet.core.native_brain.presence import PresenceContext
from velvet.core.native_brain.self_orientation import (
    PersonalityProfile,
    PreferenceProfile,
    SelfIdentity,
    SelfOrientation,
)


class NativeBrainIntegratedCycleTests(unittest.TestCase):
    def setUp(self):
        self.identity = SelfIdentity()
        self.cycle = IntegratedCognitiveCycle(self.identity)
        self.orientation = SelfOrientation(
            identity=self.identity,
            personality=PersonalityProfile(traits={"patient": 0.9}),
            preferences=PreferenceProfile(values={}),
            continuity_verified=True,
            runtime_context_verified=True,
            active_body="founder-up2",
            active_surface="vehicle",
        )

    def observation(self, simulated=False):
        return ObservationEnvelope(
            event_type="vehicle.coolant.observed",
            source="ruby.sensor",
            payload={"celsius": 94.0},
            confidence=0.95,
            simulated=simulated,
        )

    def full_context(
        self,
        *,
        presence=None,
        intent_kind=IntentKind.PROPOSE_WORK,
        consequential=False,
    ):
        return IntegratedCycleContext(
            presence=presence or PresenceContext(),
            attention=AttentionContext(
                repetition_count=5,
                corroborating_sources=2,
                historical_matches=3,
                owner_relevance=0.8,
                novelty=0.6,
            ),
            curiosity=CuriosityContext(explanation_available=True),
            judgment=JudgmentContext(
                candidate_claim="coolant rises after extended idle",
                source_reliability=0.95,
                evidence_completeness=0.95,
                freshness=1.0,
                corroborating_sources=3,
            ),
            pattern=PatternContext(
                candidate_statement="coolant tends to rise after extended idle",
                observation_key="vehicle.coolant.after-idle",
                scope="founder-up2",
                support_count=6,
                independent_contexts=4,
                corroborating_sources=3,
            ),
            expectation=ExpectationContext(
                expected_statement=(
                    "coolant may rise again when extended idle conditions return"
                ),
                triggering_conditions=("engine-idling", "cooling-load-present"),
                evidence_references=("receipt:coolant-1", "receipt:coolant-2"),
                evaluated_at=100.0,
                horizon_seconds=300.0,
                review_after_seconds=120.0,
            ),
            intent=IntentContext(
                proposed_statement="review a bounded cooling-load response",
                intent_kind=intent_kind,
                objective="reduce avoidable thermal rise",
                evidence_references=("receipt:coolant-1", "receipt:coolant-2"),
                constraints=("proposal-only", "no-actuation"),
                evaluated_at=100.0,
                expires_after_seconds=300.0,
                consequential=consequential,
                reversible=True,
            ),
        )

    def test_missing_observation_holds_and_rests(self):
        result = self.cycle.run(
            self.orientation,
            None,
            IntegratedCycleContext(),
        )

        self.assertIs(result.outcome, IntegratedCycleOutcome.HELD)
        self.assertFalse(result.ready)
        self.assertTrue(result.rested)
        self.assertIs(result.stopped_at, IntegratedCycleStage.CHECK_KEYS)
        self.assertIsNone(result.attention)
        self.assertIs(result.trace[-1].stage, IntegratedCycleStage.REST)

    def test_unverified_continuity_stops_before_presence(self):
        orientation = SelfOrientation(
            identity=self.identity,
            personality=PersonalityProfile(),
            preferences=PreferenceProfile(),
            continuity_verified=False,
            runtime_context_verified=True,
        )
        result = self.cycle.run(
            orientation,
            self.observation(),
            IntegratedCycleContext(),
        )

        self.assertIs(result.outcome, IntegratedCycleOutcome.HELD)
        self.assertIsNone(result.presence_decision)
        self.assertIn("continuity", result.reason)

    def test_presence_safety_stops_before_curiosity(self):
        result = self.cycle.run(
            self.orientation,
            self.observation(),
            IntegratedCycleContext(
                presence=PresenceContext(safety_relevant=True),
            ),
        )

        self.assertIs(result.outcome, IntegratedCycleOutcome.SAFETY_DEFERRED)
        self.assertTrue(result.safety_deferred)
        self.assertIs(result.stopped_at, IntegratedCycleStage.SAFETY)
        self.assertIsNone(result.curiosity)
        self.assertIn(
            IntegratedCycleStage.SAFETY,
            tuple(entry.stage for entry in result.trace),
        )

    def test_attention_safety_stops_before_curiosity(self):
        result = self.cycle.run(
            self.orientation,
            self.observation(),
            IntegratedCycleContext(
                attention=AttentionContext(safety_relevance=0.9),
            ),
        )

        self.assertIs(result.outcome, IntegratedCycleOutcome.SAFETY_DEFERRED)
        self.assertEqual(result.attention.priority, "critical")
        self.assertIsNone(result.curiosity)

    def test_quiet_observation_runs_every_stage_and_rests(self):
        result = self.cycle.run(
            self.orientation,
            self.observation(),
            IntegratedCycleContext(),
        )

        self.assertIs(result.outcome, IntegratedCycleOutcome.QUIET_OBSERVATION)
        self.assertIsNotNone(result.attention)
        self.assertIsNotNone(result.curiosity)
        self.assertIsNotNone(result.judgment)
        self.assertIsNotNone(result.pattern)
        self.assertIsNotNone(result.expectation)
        self.assertIsNotNone(result.intent)
        self.assertTrue(result.rested)
        self.assertIs(result.trace[-1].stage, IntegratedCycleStage.REST)

    def test_question_candidate_surfaces_without_speaking_authority(self):
        result = self.cycle.run(
            self.orientation,
            self.observation(),
            IntegratedCycleContext(
                presence=PresenceContext(addressed=True),
                curiosity=CuriosityContext(
                    contradiction=0.8,
                    owner_available=True,
                ),
                judgment=JudgmentContext(
                    candidate_claim="coolant changed unexpectedly",
                    missing_evidence=("operating-state",),
                ),
            ),
        )

        self.assertIs(result.outcome, IntegratedCycleOutcome.QUESTION_CANDIDATE)
        self.assertIs(
            result.curiosity.disposition,
            CuriosityDisposition.QUESTION_CANDIDATE,
        )
        self.assertFalse(result.speaking_authorized)
        self.assertEqual(result.authority, "none")

    def test_supported_judgment_can_finish_without_forcing_pattern(self):
        context = self.full_context()
        context = IntegratedCycleContext(
            presence=context.presence,
            attention=context.attention,
            curiosity=context.curiosity,
            judgment=context.judgment,
        )
        result = self.cycle.run(
            self.orientation,
            self.observation(),
            context,
        )

        self.assertIs(result.outcome, IntegratedCycleOutcome.JUDGMENT_READY)
        self.assertIs(result.judgment.disposition, JudgmentDisposition.READY)
        self.assertIsNone(result.pattern.candidate)

    def test_full_ladder_forms_ready_intent_candidate(self):
        result = self.cycle.run(
            self.orientation,
            self.observation(),
            self.full_context(),
        )

        self.assertIs(result.outcome, IntegratedCycleOutcome.INTENT_CANDIDATE)
        self.assertIs(result.pattern.state, PatternState.STABLE)
        self.assertIs(result.expectation.state, ExpectationState.ACTIVE)
        self.assertIs(result.intent.state, IntentState.READY_FOR_REVIEW)
        self.assertTrue(result.intent.eligible_for_downstream_review)

    def test_work_intent_requires_runtime_review_without_authority(self):
        result = self.cycle.run(
            self.orientation,
            self.observation(),
            self.full_context(intent_kind=IntentKind.PROPOSE_WORK),
        )
        candidate = result.intent.candidate

        self.assertTrue(candidate.requires_runtime_placement)
        self.assertFalse(candidate.runtime_placement_authorized)
        self.assertFalse(result.runtime_placement_authorized)
        self.assertFalse(result.execution_authorized)

    def test_consequential_intent_requires_court_review_without_authority(self):
        result = self.cycle.run(
            self.orientation,
            self.observation(),
            self.full_context(consequential=True),
        )
        candidate = result.intent.candidate

        self.assertTrue(candidate.requires_court_review)
        self.assertFalse(candidate.court_authorized)
        self.assertFalse(result.court_authorized)
        self.assertFalse(result.actuation_authorized)

    def test_actual_presence_overrides_claimed_speech_permission(self):
        context = self.full_context(intent_kind=IntentKind.INFORM)
        context = IntegratedCycleContext(
            presence=PresenceContext(),
            attention=context.attention,
            curiosity=context.curiosity,
            judgment=context.judgment,
            pattern=context.pattern,
            expectation=context.expectation,
            intent=IntentContext(
                proposed_statement=context.intent.proposed_statement,
                intent_kind=IntentKind.INFORM,
                objective=context.intent.objective,
                evidence_references=context.intent.evidence_references,
                constraints=context.intent.constraints,
                evaluated_at=context.intent.evaluated_at,
                expires_after_seconds=context.intent.expires_after_seconds,
                presence_allows_speech=True,
            ),
        )
        result = self.cycle.run(
            self.orientation,
            self.observation(),
            context,
        )

        self.assertIn("presence-review-still-required", result.intent.reasons)
        self.assertFalse(result.intent.candidate.speaking_authorized)
        self.assertFalse(result.speaking_authorized)

    def test_domain_integrity_boundary_stops_at_judgment(self):
        result = self.cycle.run(
            self.orientation,
            self.observation(),
            IntegratedCycleContext(
                judgment=JudgmentContext(integrity_aligned=False),
            ),
        )

        self.assertIs(result.outcome, IntegratedCycleOutcome.HELD)
        self.assertIs(result.stopped_at, IntegratedCycleStage.JUDGMENT)
        self.assertIs(result.judgment.disposition, JudgmentDisposition.BLOCKED)
        self.assertIsNone(result.pattern)

    def test_simulated_evidence_cannot_reach_real_pattern(self):
        result = self.cycle.run(
            self.orientation,
            self.observation(simulated=True),
            self.full_context(),
        )

        self.assertIs(result.outcome, IntegratedCycleOutcome.QUIET_OBSERVATION)
        self.assertIs(result.pattern.state, PatternState.NONE)
        self.assertIsNone(result.pattern.candidate)
        self.assertIsNone(result.expectation.candidate)
        self.assertIsNone(result.intent.candidate)

    def test_trace_order_is_complete_and_deterministic(self):
        context = self.full_context()
        first = self.cycle.run(self.orientation, self.observation(), context)
        second = self.cycle.run(self.orientation, self.observation(), context)

        self.assertEqual(first, second)
        self.assertEqual(
            tuple(entry.stage for entry in first.trace),
            (
                IntegratedCycleStage.ORIENT_SELF,
                IntegratedCycleStage.CHECK_KEYS,
                IntegratedCycleStage.OBSERVE,
                IntegratedCycleStage.PRESENCE,
                IntegratedCycleStage.ATTENTION,
                IntegratedCycleStage.CURIOSITY,
                IntegratedCycleStage.JUDGMENT,
                IntegratedCycleStage.PATTERN,
                IntegratedCycleStage.EXPECTATION,
                IntegratedCycleStage.INTENT,
                IntegratedCycleStage.CHOOSE,
                IntegratedCycleStage.REST,
            ),
        )

    def test_serialized_result_preserves_no_authority_boundary(self):
        result = self.cycle.run(
            self.orientation,
            self.observation(),
            self.full_context(),
        )
        payload = result.to_dict()

        self.assertEqual(payload["authority"], "none")
        self.assertFalse(payload["canonical"])
        self.assertTrue(payload["rested"])
        self.assertEqual(payload["intent_state"], "ready_for_review")


if __name__ == "__main__":
    unittest.main()
