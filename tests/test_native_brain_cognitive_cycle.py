# SPDX-License-Identifier: GPL-3.0-only

import unittest

from velvet.core.native_brain.cognition import CognitiveOutcome, ObservationEnvelope
from velvet.core.native_brain.cycle import CognitiveCycle, CognitiveKey, CycleStage
from velvet.core.native_brain.presence import PresenceContext
from velvet.core.native_brain.self_orientation import (
    PersonalityProfile,
    PreferenceProfile,
    SelfIdentity,
    SelfOrientation,
)


class NativeBrainCognitiveCycleTests(unittest.TestCase):
    def setUp(self):
        self.identity = SelfIdentity()
        self.cycle = CognitiveCycle(self.identity)
        self.orientation = SelfOrientation(
            identity=self.identity,
            personality=PersonalityProfile(traits={"patient": 0.9}),
            preferences=PreferenceProfile(values={}),
            continuity_verified=True,
            runtime_context_verified=True,
            active_body="founder-up2",
            active_surface="vehicle",
        )
        self.observation = ObservationEnvelope(
            event_type="vehicle.temperature.observed",
            source="ruby.sensor",
            payload={"celsius": 91.0},
            confidence=0.8,
        )

    def test_complete_cycle_returns_to_rest(self):
        result = self.cycle.run(
            self.orientation,
            self.observation,
            PresenceContext(addressed=True),
        )
        self.assertTrue(result.ready)
        self.assertTrue(result.rested)
        self.assertEqual(result.decision.outcome, CognitiveOutcome.SPEAK)
        self.assertEqual(result.trace[-1].stage, CycleStage.REST)
        self.assertEqual(result.authority, "none")

    def test_no_observation_waits_and_still_rests(self):
        result = self.cycle.run(self.orientation, None, PresenceContext())
        states = {state.key: state.satisfied for state in result.keys}
        self.assertFalse(states[CognitiveKey.OBSERVATION])
        self.assertEqual(result.decision.outcome, CognitiveOutcome.WAIT)
        self.assertTrue(result.rested)

    def test_unverified_continuity_stays_silent(self):
        orientation = SelfOrientation(
            identity=self.identity,
            personality=PersonalityProfile(),
            preferences=PreferenceProfile(),
            continuity_verified=False,
            runtime_context_verified=True,
        )
        result = self.cycle.run(orientation, self.observation, PresenceContext(addressed=True))
        self.assertEqual(result.decision.outcome, CognitiveOutcome.SILENCE)
        self.assertIn("continuity", result.decision.reason)
        self.assertFalse(result.ready)

    def test_identity_drift_blocks_normal_presence_decision(self):
        orientation = SelfOrientation(
            identity=SelfIdentity(name="Not Velvet"),
            personality=PersonalityProfile(),
            preferences=PreferenceProfile(),
            continuity_verified=True,
            runtime_context_verified=True,
        )
        result = self.cycle.run(orientation, self.observation, PresenceContext(addressed=True))
        self.assertEqual(result.decision.outcome, CognitiveOutcome.SILENCE)
        self.assertFalse(result.ready)
        self.assertEqual(result.authority, "none")

    def test_safety_presence_can_escalate_but_not_grant_authority(self):
        result = self.cycle.run(
            self.orientation,
            self.observation,
            PresenceContext(safety_relevant=True),
        )
        self.assertEqual(result.decision.outcome, CognitiveOutcome.ESCALATE)
        self.assertTrue(result.decision.interrupt)
        self.assertEqual(result.authority, "none")

    def test_trace_is_deterministic_for_same_inputs(self):
        first = self.cycle.run(self.orientation, self.observation, PresenceContext())
        second = self.cycle.run(self.orientation, self.observation, PresenceContext())
        self.assertEqual(first.decision, second.decision)
        self.assertEqual(first.keys, second.keys)
        self.assertEqual(first.trace, second.trace)


if __name__ == "__main__":
    unittest.main()
